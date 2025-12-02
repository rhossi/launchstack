from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
import uuid

from app.models.stack import Stack
from app.models.agent import Agent
from app.schemas.stack import StackCreate, StackUpdate
from app.utils.exceptions import NotFoundError, ForbiddenError
from app.utils.k8s import create_namespace, delete_namespace, get_k8s_client
from app.utils.k8s_deploy import create_postgres_deployment
from app.utils.filesystem import create_stack_directory, delete_stack_directory
from app.utils import aegra_json
from app.config import settings
import logging

logger = logging.getLogger(__name__)


async def get_stacks(
    db: AsyncSession,
    user_id: uuid.UUID,
    page: int = 1,
    limit: int = 20,
    search: Optional[str] = None,
) -> tuple[List[Stack], int]:
    query = select(Stack).options(
        selectinload(Stack.creator),
        selectinload(Stack.updater),
    ).where(Stack.created_by == user_id)
    
    if search:
        query = query.where(Stack.name.ilike(f"%{search}%"))
    
    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar() or 0
    
    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    stacks = result.scalars().all()
    
    return stacks, total


async def get_stack_by_id(db: AsyncSession, stack_id: uuid.UUID) -> Stack:
    result = await db.execute(
        select(Stack)
        .options(
            selectinload(Stack.creator),
            selectinload(Stack.updater),
            selectinload(Stack.agents).selectinload(Agent.creator),
            selectinload(Stack.agents).selectinload(Agent.updater),
        )
        .where(Stack.id == stack_id)
    )
    stack = result.scalar_one_or_none()
    if not stack:
        raise NotFoundError("Stack not found")
    return stack


async def create_stack(
    db: AsyncSession,
    stack_data: StackCreate,
    user_id: uuid.UUID,
) -> Stack:
    """Create stack record immediately with status='creating'. 
    Infrastructure setup happens in background task."""
    # Generate stack ID first so we can create namespace
    stack_id = uuid.uuid4()
    namespace = f"stack-{stack_id}"
    
    # Create stack with status='creating'
    stack = Stack(
        id=stack_id,
        name=stack_data.name,
        namespace=namespace,
        description=stack_data.description,
        status="creating",
        created_by=user_id,
        updated_by=user_id,
    )
    db.add(stack)
    await db.commit()
    
    # Reload with all relationships
    result = await db.execute(
        select(Stack)
        .options(
            selectinload(Stack.creator),
            selectinload(Stack.updater),
            selectinload(Stack.agents).selectinload(Agent.creator),
            selectinload(Stack.agents).selectinload(Agent.updater),
        )
        .where(Stack.id == stack_id)
    )
    loaded_stack = result.scalar_one()
    return loaded_stack


async def complete_stack_creation(
    stack_id: uuid.UUID,
) -> None:
    """Background task to complete stack infrastructure setup."""
    from app.database import AsyncSessionLocal
    
    # Create a new session for the background task
    async with AsyncSessionLocal() as task_db:
        try:
            # Get stack
            result = await task_db.execute(
                select(Stack).where(Stack.id == stack_id)
            )
            stack = result.scalar_one_or_none()
            if not stack:
                logger.error(f"Stack {stack_id} not found for background creation")
                return
            
            namespace = stack.namespace
            if not namespace:
                logger.error(f"Stack {stack_id} has no namespace")
                stack.status = "failed"
                await task_db.commit()
                return
            
            # Create k8s namespace
            try:
                await create_namespace(namespace)
                logger.info(f"Created k8s namespace {namespace} for stack {stack_id}")
            except Exception as e:
                logger.error(f"Failed to create k8s namespace {namespace}: {str(e)}")
                # In development, continue if k8s is not available
                if settings.environment == "development":
                    logger.warning("Continuing without k8s namespace in development mode")
                else:
                    stack.status = "failed"
                    await task_db.commit()
                    return
            
            # Deploy PostgreSQL in the namespace
            try:
                core_v1, apps_v1, _ = get_k8s_client()
                await create_postgres_deployment(
                    core_v1=core_v1,
                    apps_v1=apps_v1,
                    namespace=namespace
                )
                logger.info(f"Deployed PostgreSQL in namespace {namespace} for stack {stack_id}")
            except Exception as e:
                logger.error(f"Failed to deploy PostgreSQL in namespace {namespace}: {str(e)}")
                # In development, continue if k8s is not available
                if settings.environment == "development":
                    logger.warning("Continuing without PostgreSQL deployment in development mode")
                else:
                    stack.status = "failed"
                    await task_db.commit()
                    return
            
            # Create disk directory
            try:
                create_stack_directory(settings.agent_platform_base_path, stack_id)
                logger.info(f"Created disk directory for stack {stack_id}")
            except Exception as e:
                logger.error(f"Failed to create disk directory for stack {stack_id}: {str(e)}")
                stack.status = "failed"
                await task_db.commit()
                return
            
            # Mark as ready
            stack.status = "ready"
            await task_db.commit()
            logger.info(f"Stack {stack_id} creation completed successfully")
            
        except Exception as e:
            logger.error(f"Unexpected error completing stack creation for {stack_id}: {str(e)}")
            # Try to update status to failed
            try:
                result = await task_db.execute(
                    select(Stack).where(Stack.id == stack_id)
                )
                stack = result.scalar_one_or_none()
                if stack:
                    stack.status = "failed"
                    await task_db.commit()
            except Exception:
                logger.error(f"Failed to update stack {stack_id} status to failed")


async def update_stack(
    db: AsyncSession,
    stack_id: uuid.UUID,
    stack_data: StackUpdate,
    user_id: uuid.UUID,
) -> Stack:
    # Get stack without loading all relationships for authorization check
    result = await db.execute(
        select(Stack).where(Stack.id == stack_id)
    )
    stack = result.scalar_one_or_none()
    if not stack:
        raise NotFoundError("Stack not found")
    
    if stack.created_by != user_id:
        raise ForbiddenError("You can only update stacks you created")
    
    if stack_data.name is not None:
        stack.name = stack_data.name
    if stack_data.description is not None:
        stack.description = stack_data.description
    stack.updated_by = user_id
    
    await db.commit()
    await db.refresh(stack)
    
    # Reload with all relationships for StackDetailResponse
    result = await db.execute(
        select(Stack)
        .options(
            selectinload(Stack.creator),
            selectinload(Stack.updater),
            selectinload(Stack.agents).selectinload(Agent.creator),
            selectinload(Stack.agents).selectinload(Agent.updater),
        )
        .where(Stack.id == stack.id)
    )
    return result.scalar_one()


async def delete_stack(
    db: AsyncSession,
    stack_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    """Mark stack for deletion immediately. Actual deletion happens in background."""
    # Get stack without loading all relationships for delete check
    result = await db.execute(
        select(Stack).where(Stack.id == stack_id)
    )
    stack = result.scalar_one_or_none()
    if not stack:
        raise NotFoundError("Stack not found")
    
    # Compare UUIDs directly
    if stack.created_by != user_id:
        raise ForbiddenError("You can only delete stacks you created")
    
    # Mark as deleting immediately
    stack.status = "deleting"
    await db.commit()


async def complete_stack_deletion(
    stack_id: uuid.UUID,
) -> None:
    """Background task to complete stack deletion (delete agents from Aegra API, k8s namespace, disk, DB)."""
    from app.database import AsyncSessionLocal
    from app.models.agent import Agent
    
    # Create a new session for the background task
    async with AsyncSessionLocal() as task_db:
        try:
            # Get stack with agents
            result = await task_db.execute(
                select(Stack).where(Stack.id == stack_id)
            )
            stack = result.scalar_one_or_none()
            if not stack:
                logger.warning(f"Stack {stack_id} not found for deletion")
                return
            
            # Get all agents for this stack
            agents_result = await task_db.execute(
                select(Agent).where(Agent.stack_id == stack_id)
            )
            agents = agents_result.scalars().all()
            
            # Remove all agents from aegra.json
            for agent in agents:
                if agent.graph_id:
                    # Remove from aegra.json
                    try:
                        aegra_json.remove_graph_entry(agent.graph_id)
                        logger.info(f"Removed agent {agent.id} (graph_id: {agent.graph_id}) from aegra.json")
                    except Exception as e:
                        logger.error(f"Failed to remove agent {agent.id} from aegra.json: {str(e)}")
                        # Continue with deletion even if aegra.json update fails
            
            # Validate aegra.json after all removals
            is_valid, error_msg = aegra_json.validate_aegra_json()
            if not is_valid:
                logger.warning(f"aegra.json is corrupted after stack deletion: {error_msg}")
            
            namespace = stack.namespace
            
            # Delete k8s namespace (cascades to all agents)
            if namespace:
                try:
                    await delete_namespace(namespace)
                    logger.info(f"Deleted k8s namespace {namespace} for stack {stack_id}")
                except Exception as e:
                    logger.error(f"Failed to delete k8s namespace {namespace}: {str(e)}")
                    # Continue with deletion even if k8s fails
            
            # Delete disk directory
            try:
                delete_stack_directory(settings.agent_platform_base_path, stack_id)
                logger.info(f"Deleted disk directory for stack {stack_id}")
            except Exception as e:
                logger.error(f"Failed to delete disk directory for stack {stack_id}: {str(e)}")
                # Continue with DB deletion even if disk deletion fails
            
            # Delete from DB (cascades to agents)
            await task_db.delete(stack)
            await task_db.commit()
            logger.info(f"Stack {stack_id} deletion completed successfully")
            
        except Exception as e:
            logger.error(f"Unexpected error completing stack deletion for {stack_id}: {str(e)}")
            # Try to mark as failed or just log
            try:
                result = await task_db.execute(
                    select(Stack).where(Stack.id == stack_id)
                )
                stack = result.scalar_one_or_none()
                if stack:
                    stack.status = "failed"
                    await task_db.commit()
            except Exception:
                logger.error(f"Failed to update stack {stack_id} status to failed")

