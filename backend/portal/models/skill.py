from sqlalchemy import Column, String, Text, DateTime, JSON, Boolean, Enum
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class SkillStatus(str, enum.Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"


class Skill(Base):
    __tablename__ = "skills"

    id = Column(String(36), primary_key=True)  # UUID
    group_id = Column(String(36), nullable=False)  # 版本组ID
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True, default="⚡")
    tags = Column(JSON, nullable=True, default=list)
    folder_path = Column(String(255), nullable=True)  # 技能文件夹相对路径
    entry_script = Column(String(100), nullable=True, default="main.py")  # 入口脚本
    author = Column(String(50), nullable=True)
    version = Column(String(20), nullable=True, default="1.0.0")
    status = Column(String(20), nullable=False, default="active")  # active/deprecated
    interactions = Column(JSON, nullable=True, default=list)  # 交互配置
    # 输出配置
    output_config = Column(JSON, nullable=True, default=dict)  # 输出文件配置
    original_created_at = Column(DateTime, server_default=func.now())  # 原始创建时间（用于排序）
    created_at = Column(DateTime, server_default=func.now())  # 本版本创建时间
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    # MinIO 同步状态
    minio_synced = Column(Boolean, nullable=False, default=False)  # 是否已同步到 MinIO
    # 软删除
    deleted_at = Column(DateTime, nullable=True, index=True)  # 软删除时间戳，NULL 表示未删除
