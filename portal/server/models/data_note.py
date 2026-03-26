from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer
from sqlalchemy.sql import func
from database import Base


class DataNote(Base):
    __tablename__ = "user_data_notes"

    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), nullable=False, index=True)
    agent_id = Column(String(36), nullable=True, index=True)  # 关联的 Agent ID
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    file_type = Column(String(20), nullable=False)  # 'folder' 表示文件夹
    file_url = Column(String(500), nullable=True)   # 文件夹时为空
    file_size = Column(String(20), nullable=True)
    source_skill = Column(String(100), nullable=True)
    is_favorited = Column(Boolean, default=False)
    # 文件夹支持
    parent_id = Column(String(50), nullable=True, index=True)  # 父文件夹ID
    level = Column(Integer, default=0)  # 层级：0=根目录
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
