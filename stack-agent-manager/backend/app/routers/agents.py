from fastapi import APIRouter, Depends, status, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.dependencies import get_current_user
from app.schemas.agent import AgentUpdate, AgentResponse, AgentListPaginated
from app.services import agent as agent_service

router = APIRouter(prefix="/api", tags=["agents"])


@router.get("/stacks/{stack_id}/agents", response_model=AgentListPaginated)
async def list_agents(
    stack_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import uuid
    agents, total = await agent_service.get_agents_by_stack(db, uuid.UUID(stack_id), current_user.id)
    return {
        "items": agents,
        "total": total,
    }


@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import uuid
    agent = await agent_service.get_agent_by_id(db, uuid.UUID(agent_id))
    return agent


@router.post("/stacks/{stack_id}/agents", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    stack_id: str,
    name: str = Form(...),
    description: str | None = Form(None),
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import uuid
    from app.schemas.agent import AgentCreate
    
    import tempfile
    import os
    
    # Validate file is a zip
    if not file.filename or not file.filename.endswith('.zip'):
        raise ValueError("File must be a .zip file")
    
    # Create AgentCreate schema from form data
    agent_data = AgentCreate(name=name, description=description)
    
    # Create agent in DB immediately (fast operation - no file I/O)
    agent = await agent_service.create_agent(
        db, 
        uuid.UUID(stack_id), 
        agent_data, 
        current_user.id
    )
    
    # Save uploaded file to temporary location for background processing
    # This allows the request to return immediately while the background task
    # handles all file operations (reading, saving, extracting, updating aegra.json)
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    try:
        # Stream file to temp location (non-blocking, fast)
        content = await file.read()
        temp_file.write(content)
        temp_file_path = temp_file.name
    finally:
        temp_file.close()
    
    # Add background task to complete agent creation (with temp file path)
    # All heavy operations happen in background:
    # - Read temp file
    # - Save to agent directory
    # - Extract zip
    # - Detect agent slug
    # - Update aegra.json
    # - Update agent status
    background_tasks.add_task(
        agent_service.complete_agent_creation,
        agent.id,
        temp_file_path
    )
    
    return agent


@router.put("/agents/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    agent_data: AgentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import uuid
    agent = await agent_service.update_agent(db, uuid.UUID(agent_id), agent_data, current_user.id)
    return agent


@router.delete("/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import uuid
    # Mark agent for deletion and add background task for actual deletion
    await agent_service.delete_agent(db, uuid.UUID(agent_id), current_user.id)
    
    # Add background task to complete deletion
    background_tasks.add_task(
        agent_service.complete_agent_deletion,
        uuid.UUID(agent_id)
    )
    
    return None

