from sqlalchemy import Column, String, Text, DateTime, JSON, Integer, Enum
from sqlalchemy.sql import func
from database import Base
import enum


class ExecutionStatus(enum.Enum):
    pending = "pending"
    running = "running"
    paused = "paused"
    completed = "completed"
    failed = "failed"


class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"

    id = Column(String(50), primary_key=True)
    workflow_id = Column(String(50), nullable=False)
    status = Column(String(20), default="pending")
    current_step = Column(Integer, default=0)
    total_steps = Column(Integer, default=0)
    context = Column(JSON, nullable=True, default=dict)
    pending_interaction = Column(JSON, nullable=True)
    completed_steps = Column(JSON, nullable=True, default=list)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
