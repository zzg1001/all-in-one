from sqlalchemy import Column, String, Text, DateTime, JSON, Integer, Enum, Index
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class MessageRole(str, enum.Enum):
    USER = "user"
    AGENT = "agent"


class ChatSession(Base):
    """聊天会话表"""
    __tablename__ = "chat_sessions"

    id = Column(String(36), primary_key=True)  # UUID
    user_id = Column(String(50), nullable=False, default="default", index=True)
    title = Column(String(200), nullable=True)  # 会话标题，从首条消息自动提取
    message_count = Column(Integer, default=0)  # 消息数量
    skill_names = Column(JSON, nullable=True, default=list)  # 涉及的技能名称列表
    last_message_at = Column(DateTime, nullable=True)  # 最后消息时间
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_sessions_user_time', 'user_id', 'last_message_at'),
    )


class ChatMessage(Base):
    """聊天消息表"""
    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True)  # UUID
    session_id = Column(String(36), nullable=False, index=True)
    role = Column(String(10), nullable=False)  # user / agent
    content = Column(Text, nullable=False)
    # 元数据：技能规划、流程边、附件等
    extra_data = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index('idx_messages_session_time', 'session_id', 'created_at'),
    )
