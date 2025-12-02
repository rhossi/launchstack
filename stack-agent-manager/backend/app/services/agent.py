from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
import uuid
import logging
from pathlib import Path

from app.models.agent import Agent
from app.models.stack import Stack
from app.schemas.agent import AgentCreate, AgentUpdate
from app.utils.exceptions import NotFoundError, ForbiddenError, ConflictError
from app.utils.filesystem import (
    create_agent_directory,
    extract_agent_zip,
    delete_agent_directory,
    detect_agent_slug,
    get_agent_base_path,
)
from app.utils import aegra_json
from app.config import settings

logger = logging.getLogger(__name__)

async def get_agents_by_stack(
    db: AsyncSession,
    stack_id: uuid.UUID,
    user_id: uuid.UUID,
) -> tuple[List[Agent], int]:
    # Verify stack exists and belongs to user
    result = await db.execute(
        select(Stack).where(Stack.id == stack_id, Stack.created_by == user_id)
    )
    stack = result.scalar_one_or_none()
    if not stack:
        raise NotFoundError("Stack not found")
    
    query = select(Agent).options(
        selectinload(Agent.creator),
        selectinload(Agent.updater),
    ).where(Agent.stack_id == stack_id)
    
    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar() or 0
    
    result = await db.execute(query)
    agents = result.scalars().all()
    
    return agents, total


async def get_agent_by_id(db: AsyncSession, agent_id: uuid.UUID) -> Agent:
    result = await db.execute(
        select(Agent)
        .options(
            selectinload(Agent.creator),
            selectinload(Agent.updater),
            selectinload(Agent.stack),
        )
        .where(Agent.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise NotFoundError("Agent not found")
    return agent


async def create_agent(
    db: AsyncSession,
    stack_id: uuid.UUID,
    agent_data: AgentCreate,
    user_id: uuid.UUID,
) -> Agent:
    """Create agent in DB. Background task handles all file operations and setup."""
    # Load stack
    result = await db.execute(select(Stack).where(Stack.id == stack_id))
    stack = result.scalar_one_or_none()
    if not stack:
        raise NotFoundError("Stack not found")
    
    existing_result = await db.execute(
        select(Agent).where(
            Agent.stack_id == stack_id,
            Agent.name == agent_data.name
        )
    )
    if existing_result.scalar_one_or_none():
        raise ConflictError("Agent with this name already exists in this stack")
    
    # Create agent in DB with status "creating"
    # All file operations will be handled by background task
    agent = Agent(
        stack_id=stack_id,
        name=agent_data.name,
        description=agent_data.description,
        status="creating",
        created_by=user_id,
        updated_by=user_id,
        # These will be set by background task:
        # graph_id, api_url, ui_url, disk_path are None initially
    )
    db.add(agent)
    await db.commit()
    
    # Reload with all relationships
    result = await db.execute(
        select(Agent)
        .options(
            selectinload(Agent.creator),
            selectinload(Agent.updater),
        )
        .where(Agent.id == agent.id)
    )
    return result.scalar_one()


async def complete_agent_creation(
    agent_id: uuid.UUID,
    temp_file_path: str,
) -> None:
    """Background task to complete agent creation (save file, extract, detect slug, create assistant via API).
    
    All file operations happen here in the background, ensuring the API response returns immediately.
    """
    from app.database import AsyncSessionLocal
    import os
    
    # Create a new session for the background task
    async with AsyncSessionLocal() as task_db:
        try:
            # Get agent
            result = await task_db.execute(
                select(Agent).where(Agent.id == agent_id)
            )
            agent = result.scalar_one_or_none()
            if not agent:
                logger.error(f"Agent {agent_id} not found for background creation")
                # Clean up temp file
                try:
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
                except Exception:
                    pass
                return
            
            if agent.status != "creating":
                logger.warning(f"Agent {agent_id} is not in creating status, skipping")
                # Clean up temp file
                try:
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
                except Exception:
                    pass
                return
            
            stack_id = agent.stack_id
            
            try:
                # 1. Create directory
                logger.info(f"Step 1: Creating directory for agent {agent_id}")
                create_agent_directory(settings.agent_platform_base_path, stack_id, agent_id)
                
                # 2. Copy temp file to agent directory
                logger.info(f"Step 2: Copying zip file from temp location for agent {agent_id}")
                agent_path = get_agent_base_path(settings.agent_platform_base_path, stack_id, agent_id)
                zip_path = agent_path / "agent.zip"
                
                # Verify temp file exists and has content
                if not os.path.exists(temp_file_path):
                    raise FileNotFoundError(f"Temp file not found: {temp_file_path}")
                if os.path.getsize(temp_file_path) == 0:
                    raise ValueError("Temp file is empty")
                
                # Copy temp file to final location
                import shutil
                shutil.copy2(temp_file_path, zip_path)
                logger.info(f"Copied zip file to {zip_path}")
                
                # Clean up temp file immediately after copying
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temp file {temp_file_path}: {e}")
                
                # 3. Extract zip to extracted/ directory
                logger.info(f"Step 3: Extracting zip for agent {agent_id}")
                extracted_path = extract_agent_zip(settings.agent_platform_base_path, stack_id, agent_id)
                
                # 4. Detect agent slug from extracted structure
                logger.info(f"Step 4: Detecting agent slug for agent {agent_id}")
                agent_slug = detect_agent_slug(extracted_path)
                logger.info(f"Detected agent slug: {agent_slug}")
                
                # 5. Compute graph_id and graph_path
                graph_id = f"{stack_id}__{agent_id}"
                graph_path = f"./graphs/{stack_id}/agents/{agent_id}/extracted/{agent_slug}/graph.py:graph"
                logger.info(f"Step 5: Computed graph_id={graph_id}, graph_path={graph_path}")
                
                # Verify graph.py file exists at the computed path
                graph_file_path = Path(settings.agent_platform_base_path) / "stacks" / str(stack_id) / "agents" / str(agent_id) / "extracted" / agent_slug / "graph.py"
                if not graph_file_path.exists():
                    raise FileNotFoundError(f"Graph file not found at expected path: {graph_file_path}")
                logger.info(f"Verified graph.py exists at: {graph_file_path}")
                
                # 6. Update aegra.json
                logger.info(f"Step 6: Updating aegra.json for agent {agent_id}")
                aegra_json.update_graph_entry(graph_id, graph_path)
                logger.info(f"Successfully updated aegra.json with graph_id: {graph_id}")
                
                # 7. Validate aegra.json to ensure it's not corrupted
                logger.info(f"Step 7: Validating aegra.json for agent {agent_id}")
                is_valid, error_msg = aegra_json.validate_aegra_json()
                
                if not is_valid:
                    raise Exception(f"aegra.json is corrupted after update: {error_msg}")
                
                logger.info(f"aegra.json validated successfully for agent {agent_id}")
                
                # 8. Update agent fields
                logger.info(f"Step 8: Updating agent fields for agent {agent_id}")
                agent.disk_path = str(extracted_path)
                agent.graph_id = graph_id
                # Use public URL for end users (localhost), not internal Docker service name
                agent.api_url = settings.aegra_api_public_url
                agent.ui_url = f"{settings.chat_ui_base_url}/?apiUrl={settings.aegra_api_public_url}&assistantId={graph_id}"
                agent.status = "ready"
                
                await task_db.commit()
                logger.info(f"Agent {agent_id} creation completed successfully")
                
            except Exception as e:
                logger.error(f"Failed to complete agent creation for {agent_id}: {str(e)}")
                # Mark agent as failed
                agent.status = "failed"
                await task_db.commit()
                
                # Clean up disk directory
                try:
                    delete_agent_directory(settings.agent_platform_base_path, stack_id, agent_id)
                except Exception:
                    pass
                
        except Exception as e:
            logger.error(f"Unexpected error completing agent creation for {agent_id}: {str(e)}", exc_info=True)
            # Clean up temp file if it still exists
            try:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            except Exception:
                pass


async def update_agent(
    db: AsyncSession,
    agent_id: uuid.UUID,
    agent_data: AgentUpdate,
    user_id: uuid.UUID,
) -> Agent:
    agent = await get_agent_by_id(db, agent_id)
    
    if agent.created_by != user_id:
        raise ForbiddenError("You can only update agents you created")
    
    if agent_data.name is not None:
        existing_result = await db.execute(
            select(Agent).where(
                Agent.stack_id == agent.stack_id,
                Agent.name == agent_data.name,
                Agent.id != agent_id
            )
        )
        if existing_result.scalar_one_or_none():
            raise ConflictError("Agent with this name already exists in this stack")
        agent.name = agent_data.name
    
    if agent_data.description is not None:
        agent.description = agent_data.description
    
    agent.updated_by = user_id
    
    await db.commit()
    await db.refresh(agent)
    
    result = await db.execute(
        select(Agent)
        .options(
            selectinload(Agent.creator),
            selectinload(Agent.updater),
        )
        .where(Agent.id == agent.id)
    )
    return result.scalar_one()


async def delete_agent(
    db: AsyncSession,
    agent_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    """Mark agent for deletion immediately. Actual deletion happens in background."""
    agent = await get_agent_by_id(db, agent_id)
    
    if agent.created_by != user_id:
        raise ForbiddenError("You can only delete agents you created")
    
    # Mark as deleting immediately
    agent.status = "deleting"
    await db.commit()


async def complete_agent_deletion(
    agent_id: uuid.UUID,
) -> None:
    """Background task to complete agent deletion (delete from Aegra API, delete disk, delete from DB)."""
    from app.database import AsyncSessionLocal
    
    # Create a new session for the background task
    async with AsyncSessionLocal() as task_db:
        try:
            # Get agent
            result = await task_db.execute(
                select(Agent).where(Agent.id == agent_id)
            )
            agent = result.scalar_one_or_none()
            if not agent:
                logger.warning(f"Agent {agent_id} not found for deletion")
                return
            
            stack_id = agent.stack_id
            graph_id = agent.graph_id
            
            # Remove from aegra.json if graph_id exists
            if graph_id:
                try:
                    aegra_json.remove_graph_entry(graph_id)
                    logger.info(f"Removed agent {agent_id} from aegra.json")
                    
                    # Validate aegra.json after removal
                    is_valid, error_msg = aegra_json.validate_aegra_json()
                    if not is_valid:
                        logger.warning(f"aegra.json is corrupted after removal: {error_msg}")
                except Exception as e:
                    logger.error(f"Failed to remove agent {agent_id} from aegra.json: {str(e)}")
                    # Continue with deletion even if aegra.json update fails
            
            # Delete disk directory
            if agent.disk_path:
                try:
                    delete_agent_directory(settings.agent_platform_base_path, stack_id, agent_id)
                    logger.info(f"Deleted disk directory for agent {agent_id}")
                except Exception as e:
                    logger.error(f"Failed to delete disk directory for agent {agent_id}: {str(e)}")
                    # Continue with DB deletion even if disk deletion fails
            
            # Delete from DB
            await task_db.delete(agent)
            await task_db.commit()
            logger.info(f"Agent {agent_id} deletion completed successfully")
            
        except Exception as e:
            logger.error(f"Unexpected error completing agent deletion for {agent_id}: {str(e)}")

