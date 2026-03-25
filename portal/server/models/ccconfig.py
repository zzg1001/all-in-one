"""
CCConfig Model - Claude 配置模型
与 Admin 共享同一张数据库表
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime
from datetime import datetime
from database import Base


class CCConfig(Base):
    """Claude 配置模型"""
    __tablename__ = "cc_configs"

    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    model_id = Column(String(50), nullable=False)
    api_key = Column(String(500), nullable=False)
    base_url = Column(String(200), nullable=True)
    max_tokens = Column(Integer, default=4096)
    temperature = Column(Float, default=0.7)
    top_p = Column(Float, default=1.0)
    system_prompt = Column(Text, nullable=True)
    extra_params = Column(Text, nullable=True)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
