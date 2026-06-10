from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class ExtractRecord(Base):
    """企业信息提取 - 保存的历史记录"""
    __tablename__ = "user_extract_records"

    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), nullable=False, index=True, default="anonymous")  # 仍存便于溯源，列表全局共享不按它过滤
    company_name = Column(String(255), nullable=True, index=True)
    credit_code = Column(String(50), nullable=True)
    data = Column(JSON, nullable=True)  # 完整企业信息 dict（中文键）
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    # 软删除：NULL 表示未删除
    deleted_at = Column(DateTime, nullable=True, index=True)
