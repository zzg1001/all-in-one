"""用户反馈模型"""
from sqlalchemy import Column, String, Text, DateTime, Index
from sqlalchemy.sql import func
from app.core.database import Base


class UserFeedback(Base):
    """用户反馈表

    用于收集用户在使用过程中的问题反馈、Bug 报告和建议。
    """
    __tablename__ = "user_feedbacks"

    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), nullable=False, index=True)  # 用户ID
    session_id = Column(String(50), nullable=True)  # 关联的会话ID（可选）
    agent_id = Column(String(50), nullable=True)  # 关联的Agent ID
    agent_name = Column(String(100), nullable=True)  # Agent名称（冗余存储，方便展示）
    feedback_type = Column(String(20), nullable=False)  # 'bug' | 'suggestion' | 'other'
    title = Column(String(200), nullable=False)  # 反馈标题
    description = Column(Text, nullable=True)  # 详细描述
    status = Column(String(20), default='pending')  # pending/processing/resolved/closed
    admin_notes = Column(Text, nullable=True)  # 管理员备注
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    __table_args__ = (
        # 按用户和状态查询的索引
        Index('idx_feedback_user_status', 'user_id', 'status'),
        # 按状态和创建时间查询的索引（管理端列表）
        Index('idx_feedback_status_created', 'status', 'created_at'),
        # 按Agent查询的索引
        Index('idx_feedback_agent', 'agent_id'),
    )
