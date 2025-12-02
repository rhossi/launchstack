from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.database import Base


class Agent(Base):
    __tablename__ = "agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stack_id = Column(UUID(as_uuid=True), ForeignKey("stacks.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="pending", index=True)
    graph_id = Column(String(255), nullable=True, index=True)
    api_url = Column(String(500), nullable=True)
    ui_url = Column(String(500), nullable=True)
    disk_path = Column(String(1000), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("stack_id", "name", name="uq_agent_stack_name"),)

    stack = relationship("Stack", back_populates="agents")
    creator = relationship("User", foreign_keys=[created_by], back_populates="agents_created")
    updater = relationship("User", foreign_keys=[updated_by], back_populates="agents_updated")

