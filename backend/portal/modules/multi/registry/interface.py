"""
Registry 模块接口定义
"""

from typing import Protocol, List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class ServiceStatus(str, Enum):
    """服务状态"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ServiceInfo(BaseModel):
    """服务信息"""
    agent_id: str
    name: str
    description: str = ""
    capabilities: List[str] = []
    endpoint: Optional[str] = None
    status: ServiceStatus = ServiceStatus.UNKNOWN
    metadata: Dict[str, Any] = {}
    registered_at: datetime = datetime.now()
    last_heartbeat: Optional[datetime] = None


class IRegistryModule(Protocol):
    """Registry 模块接口"""

    async def register(
        self,
        agent_id: str,
        name: str,
        capabilities: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """注册服务"""
        ...

    async def deregister(self, agent_id: str) -> bool:
        """注销服务"""
        ...

    async def heartbeat(self, agent_id: str) -> bool:
        """发送心跳"""
        ...

    async def discover(
        self,
        capability: Optional[str] = None,
        status: Optional[ServiceStatus] = None,
    ) -> List[ServiceInfo]:
        """服务发现"""
        ...

    async def get_service(self, agent_id: str) -> Optional[ServiceInfo]:
        """获取服务信息"""
        ...

    async def health_check(self, agent_id: str) -> ServiceStatus:
        """健康检查"""
        ...
