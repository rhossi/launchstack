from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, model_validator
import uuid

from app.schemas.user import UserInfo
from app.schemas.agent import AgentResponse


class StackBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)


class StackCreate(StackBase):
    pass


class StackUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)


class StackResponse(StackBase):
    id: uuid.UUID
    namespace: Optional[str]
    status: str
    created_at: datetime
    created_by: UserInfo
    updated_at: datetime
    updated_by: UserInfo

    @model_validator(mode='before')
    @classmethod
    def map_relationships(cls, data):
        # If data is a SQLAlchemy model instance, map relationships
        if hasattr(data, 'creator') and hasattr(data, 'updater'):
            result = {
                'id': data.id,
                'name': data.name,
                'namespace': getattr(data, 'namespace', None),
                'status': getattr(data, 'status', 'ready'),
                'description': data.description,
                'created_at': data.created_at,
                'created_by': data.creator,
                'updated_at': data.updated_at,
                'updated_by': data.updater,
            }
            # Don't access 'agents' here to avoid lazy loading outside async context
            # StackDetailResponse will handle agents via from_attributes when loaded via selectinload
            return result
        return data

    class Config:
        from_attributes = True


class StackListResponse(StackResponse):
    agent_count: int = 0


class StackDetailResponse(StackResponse):
    agents: List[AgentResponse] = []
    
    @model_validator(mode='before')
    @classmethod
    def map_relationships_with_agents(cls, data):
        # First, get the base mapping from parent class
        if hasattr(data, 'creator') and hasattr(data, 'updater'):
            result = {
                'id': data.id,
                'name': data.name,
                'namespace': getattr(data, 'namespace', None),
                'status': getattr(data, 'status', 'ready'),
                'description': data.description,
                'created_at': data.created_at,
                'created_by': data.creator,
                'updated_at': data.updated_at,
                'updated_by': data.updater,
            }
            # Check if agents are already loaded (eagerly loaded via selectinload)
            # Use inspect to check without triggering lazy load
            try:
                from sqlalchemy import inspect as sa_inspect
                insp = sa_inspect(data)
                if 'agents' in insp.attrs:
                    # Relationship exists, check if it's loaded
                    agents_attr = insp.attrs.agents
                    if agents_attr.loaded_value is not None:
                        # Agents are already loaded, include them
                        result['agents'] = agents_attr.loaded_value
                    else:
                        # Not loaded, use empty list
                        result['agents'] = []
                else:
                    result['agents'] = []
            except Exception:
                # If inspection fails, default to empty list
                result['agents'] = []
            return result
        return data


class StackListPaginated(BaseModel):
    items: List[StackListResponse]
    total: int
    page: int
    limit: int
    pages: int

