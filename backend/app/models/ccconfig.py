"""
CCConfig Model - Claude 配置模型
使用 MySQL 存储（与 Portal 共享数据库）
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime
from datetime import datetime

from app.core.database import Base


class CCConfig(Base):
    """Claude 配置模型"""
    __tablename__ = "cc_configs"

    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False, comment="配置名称")
    description = Column(String(500), nullable=True, comment="配置描述")
    model_id = Column(String(50), nullable=False, comment="模型ID: claude-opus-4-5, claude-sonnet-4")
    api_key = Column(String(500), nullable=False, comment="API Key")
    base_url = Column(String(200), nullable=True, comment="自定义 Base URL")
    max_tokens = Column(Integer, default=4096, comment="最大 Token 数")
    temperature = Column(Float, default=0.7, comment="温度参数")
    top_p = Column(Float, default=1.0, comment="Top P 参数")
    system_prompt = Column(Text, nullable=True, comment="系统提示词")
    extra_params = Column(Text, nullable=True, comment="额外参数 JSON")
    is_active = Column(Boolean, default=False, comment="是否启用")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    def to_dict(self):
        """转换为字典"""
        import json
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "model_id": self.model_id,
            "api_key": self.api_key,
            "base_url": self.base_url,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "system_prompt": self.system_prompt,
            "extra_params": json.loads(self.extra_params) if self.extra_params else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
