"""
Agent 数据库模型
包含 Agent 主表、模块配置、记忆存储、执行记录
"""

from sqlalchemy import Column, String, Text, DateTime, JSON, Boolean, Integer, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class AgentStatus(str, enum.Enum):
    """Agent状态"""
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"


class Agent(Base):
    """Agent 主表"""
    __tablename__ = "agents"

    id = Column(String(36), primary_key=True)  # UUID
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True, default="")
    icon = Column(String(50), nullable=True, default="🤖")
    category = Column(String(50), nullable=True, default="通用助手")
    system_prompt = Column(Text, nullable=True, default="")

    # 模型配置
    model = Column(String(100), nullable=False, default="claude-opus-4-5")
    temperature = Column(Float, nullable=False, default=0.7)
    max_tokens = Column(Integer, nullable=False, default=4096)

    # 工具和技能（JSON数组）
    tools = Column(JSON, nullable=True, default=list)
    skills = Column(JSON, nullable=True, default=list)

    # 模块配置（JSON对象，存储各模块配置）
    module_configs = Column(JSON, nullable=True, default=dict)

    # 状态和元信息
    status = Column(String(20), nullable=False, default="draft")
    author = Column(String(100), nullable=True, default="User")
    version = Column(String(20), nullable=True, default="1.0.0")
    usage_count = Column(Integer, nullable=False, default=0)

    # 时间戳
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    memories = relationship("AgentMemory", back_populates="agent", cascade="all, delete-orphan")
    executions = relationship("AgentExecution", back_populates="agent", cascade="all, delete-orphan")


class AgentMemory(Base):
    """Agent 记忆存储"""
    __tablename__ = "agent_memories"

    id = Column(String(36), primary_key=True)  # UUID
    agent_id = Column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)

    # 记忆类型和内容
    memory_type = Column(String(50), nullable=False, default="conversation")  # conversation, vector, context
    content = Column(Text, nullable=False)
    extra_data = Column(JSON, nullable=True, default=dict)  # 额外元数据

    # 向量存储（可选）
    embedding = Column(JSON, nullable=True)  # 向量嵌入
    embedding_model = Column(String(100), nullable=True)

    # 时间戳和过期
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=True)  # 过期时间（可选）

    # 关系
    agent = relationship("Agent", back_populates="memories")


class AgentExecution(Base):
    """Agent 执行记录"""
    __tablename__ = "agent_executions"

    id = Column(String(36), primary_key=True)  # UUID
    agent_id = Column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)

    # 执行信息
    execution_type = Column(String(50), nullable=False, default="chat")  # chat, task, workflow
    status = Column(String(20), nullable=False, default="running")  # pending, running, completed, failed

    # 输入输出
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)

    # 模块追踪
    modules_used = Column(JSON, nullable=True, default=list)  # 使用的模块列表
    module_metrics = Column(JSON, nullable=True, default=dict)  # 各模块的执行指标

    # Token 使用
    input_tokens = Column(Integer, nullable=True, default=0)
    output_tokens = Column(Integer, nullable=True, default=0)
    total_tokens = Column(Integer, nullable=True, default=0)

    # 性能
    latency_ms = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)

    # 时间戳
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    agent = relationship("Agent", back_populates="executions")
