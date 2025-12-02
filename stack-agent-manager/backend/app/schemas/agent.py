from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, model_validator
import uuid

from app.schemas.user import UserInfo


class AgentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)


class AgentResponse(AgentBase):
    id: uuid.UUID
    stack_id: uuid.UUID
    status: str
    api_url: Optional[str]
    ui_url: Optional[str]
    disk_path: Optional[str]
    created_at: datetime
    created_by: UserInfo
    updated_at: datetime
    updated_by: UserInfo

    @model_validator(mode='before')
    @classmethod
    def map_relationships(cls, data):
        # If data is a SQLAlchemy model instance, map relationships
        if hasattr(data, 'creator') and hasattr(data, 'updater'):
            return {
                'id': data.id,
                'stack_id': data.stack_id,
                'name': data.name,
                'description': data.description,
                'status': getattr(data, 'status', 'pending'),
                'api_url': getattr(data, 'api_url', None),
                'ui_url': getattr(data, 'ui_url', None),
                'disk_path': getattr(data, 'disk_path', None),
                'created_at': data.created_at,
                'created_by': data.creator,
                'updated_at': data.updated_at,
                'updated_by': data.updater,
            }
        return data

    class Config:
        from_attributes = True


class AgentListPaginated(BaseModel):
    items: List[AgentResponse]
    total: int

