from sqlalchemy import Column, String, DateTime, Enum, UniqueConstraint, Index
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class ItemType(enum.Enum):
    skill = "skill"
    workflow = "workflow"


class UserFavorite(Base):
    """用户收藏表

    设计考虑：
    - user_id: 预留给用户系统，当前使用客户端生成的匿名ID
    - item_type: 支持收藏技能和子流程
    - 唯一约束防止重复收藏
    """
    __tablename__ = "user_favorites"

    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), nullable=False, index=True)  # 将来关联用户表
    item_type = Column(String(20), nullable=False)  # 'skill' | 'workflow'
    item_id = Column(String(50), nullable=False)  # 技能或子流程的ID
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        # 同一用户不能重复收藏同一项目
        UniqueConstraint('user_id', 'item_type', 'item_id', name='uq_user_favorite'),
        # 按用户查询的索引
        Index('idx_user_favorites', 'user_id', 'item_type'),
    )
