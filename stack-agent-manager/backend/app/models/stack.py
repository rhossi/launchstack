from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.database import Base


class Stack(Base):
    __tablename__ = "stacks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    namespace = Column(String(255), nullable=True, unique=True, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="creating", index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    creator = relationship("User", foreign_keys=[created_by], back_populates="stacks_created")
    updater = relationship("User", foreign_keys=[updated_by], back_populates="stacks_updated")
    agents = relationship("Agent", back_populates="stack", cascade="all, delete-orphan")

