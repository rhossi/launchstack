from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    stacks_created = relationship("Stack", foreign_keys="Stack.created_by", back_populates="creator")
    stacks_updated = relationship("Stack", foreign_keys="Stack.updated_by", back_populates="updater")
    agents_created = relationship("Agent", foreign_keys="Agent.created_by", back_populates="creator")
    agents_updated = relationship("Agent", foreign_keys="Agent.updated_by", back_populates="updater")

