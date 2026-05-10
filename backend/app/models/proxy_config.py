"""
ProxyConfig Model - API 代理配置模型
用于配置 Anthropic API 到其他模型（如 Qwen）的代理转换
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime
from datetime import datetime

from app.core.database import Base


class ProxyConfig(Base):
    """API 代理配置"""
    __tablename__ = "proxy_configs"

    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False, comment="配置名称")
    description = Column(String(500), nullable=True, comment="配置描述")

    # 代理类型
    proxy_type = Column(String(50), default="anthropic_to_openai", comment="代理类型")

    # 目标 API 配置
    target_base_url = Column(String(500), nullable=False, comment="目标 API Base URL")
    target_api_key = Column(String(500), nullable=False, comment="目标 API Key")
    target_model = Column(String(100), nullable=False, comment="目标模型 ID")

    # 代理服务配置
    proxy_port = Column(Integer, default=4000, comment="代理监听端口")
    proxy_path = Column(String(100), default="/v1/messages", comment="代理路径")

    # 代理地址（对外，用于配置客户端）
    proxy_url = Column(String(500), nullable=True, comment="代理地址")
    # 对外模型名（如 claude-3-opus）
    proxy_model = Column(String(100), nullable=True, comment="对外模型名")

    # 参数配置
    max_tokens = Column(Integer, default=4096, comment="默认最大 Token")
    temperature = Column(Float, default=0.7, comment="默认温度")

    # 状态
    is_enabled = Column(Boolean, default=False, comment="是否启用")
    is_running = Column(Boolean, default=False, comment="是否正在运行")
    pid = Column(Integer, nullable=True, comment="运行中的进程PID")

    # 时间戳
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        port = self.proxy_port or 4000
        return {
            "id": self.id,
            "name": self.name or "",
            "description": self.description or "",
            "proxy_type": self.proxy_type or "anthropic_to_openai",
            "target_base_url": self.target_base_url or "",
            "target_api_key": self.target_api_key or "",  # 完整显示
            "target_model": self.target_model or "",
            "proxy_port": port,
            "proxy_path": self.proxy_path or "/v1/messages",
            "proxy_url": self.proxy_url or f"http://localhost:{port}",
            "proxy_model": self.proxy_model or "claude-sonnet-4-20250514",
            "max_tokens": self.max_tokens or 4096,
            "temperature": self.temperature or 0.7,
            "is_enabled": self.is_enabled or False,
            "is_running": self.is_running or False,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_dict_full(self):
        """包含完整 API Key 的字典（仅内部使用）"""
        d = self.to_dict()
        d["target_api_key"] = self.target_api_key or ""
        return d
