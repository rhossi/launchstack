from typing import Optional
from fastapi import APIRouter, Depends, Query, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
import math

from app.database import get_db
from app.models.user import User
from app.models.stack import Stack
from app.models.agent import Agent
from app.dependencies import get_current_user
from app.schemas.stack import (
    StackCreate,
    StackUpdate,
    StackDetailResponse,
    StackListPaginated,
)
from app.services import stack as stack_service
from app.utils.exceptions import NotFoundError

router = APIRouter(prefix="/api/stacks", tags=["stacks"])


@router.get("", response_model=StackListPaginated)
async def list_stacks(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stacks, total = await stack_service.get_stacks(db, current_user.id, page, limit, search)
    pages = math.ceil(total / limit) if total > 0 else 0
    
    # Add agent_count to each stack and convert to Pydantic models
    from app.models.agent import Agent
    from app.schemas.stack import StackListResponse
    from sqlalchemy import select, func
    
    items = []
    for stack in stacks:
        agent_count_result = await db.execute(
            select(func.count(Agent.id)).where(Agent.stack_id == stack.id)
        )
        agent_count = agent_count_result.scalar() or 0
        
        # Use Pydantic model_validate to properly convert SQLAlchemy models to Pydantic
        # This ensures proper serialization of relationships (creator, updater -> UserInfo)
        stack_response = StackListResponse.model_validate(stack)
        stack_response.agent_count = agent_count
        items.append(stack_response)
    
    return StackListPaginated(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


@router.get("/{stack_id}", response_model=StackDetailResponse)
async def get_stack(
    stack_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import uuid
    
    # Get stack with ownership check and load relationships
    result = await db.execute(
        select(Stack)
        .options(
            selectinload(Stack.creator),
            selectinload(Stack.updater),
            selectinload(Stack.agents).selectinload(Agent.creator),
            selectinload(Stack.agents).selectinload(Agent.updater),
        )
        .where(Stack.id == uuid.UUID(stack_id), Stack.created_by == current_user.id)
    )
    stack = result.scalar_one_or_none()
    if not stack:
        raise NotFoundError("Stack not found")
    
    return stack


@router.post("", response_model=StackDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_stack(
    stack_data: StackCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Create stack record immediately with status='creating'
    stack = await stack_service.create_stack(db, stack_data, current_user.id)
    
    # Add background task to complete infrastructure setup
    background_tasks.add_task(
        stack_service.complete_stack_creation,
        stack.id
    )
    
    return stack


@router.put("/{stack_id}", response_model=StackDetailResponse)
async def update_stack(
    stack_id: str,
    stack_data: StackUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import uuid
    stack = await stack_service.update_stack(db, uuid.UUID(stack_id), stack_data, current_user.id)
    return stack


@router.delete("/{stack_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stack(
    stack_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import uuid
    # Mark stack as deleting and add background task for actual deletion
    await stack_service.delete_stack(db, uuid.UUID(stack_id), current_user.id)
    
    # Add background task to complete deletion
    background_tasks.add_task(
        stack_service.complete_stack_deletion,
        uuid.UUID(stack_id)
    )
    
    return None

