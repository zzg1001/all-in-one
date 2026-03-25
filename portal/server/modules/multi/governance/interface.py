"""
Governance 模块接口定义
"""

from typing import Protocol, List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class PermissionLevel(str, Enum):
    """权限级别"""
    NONE = "none"
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"


class AuditAction(str, Enum):
    """审计动作类型"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    LOGIN = "login"
    LOGOUT = "logout"


class Permission(BaseModel):
    """权限定义"""
    resource: str  # 资源标识
    level: PermissionLevel
    conditions: Dict[str, Any] = {}  # 条件限制


class AuditLog(BaseModel):
    """审计日志"""
    id: str
    timestamp: datetime
    agent_id: str
    user_id: Optional[str] = None
    action: AuditAction
    resource: str
    details: Dict[str, Any] = {}
    success: bool = True
    ip_address: Optional[str] = None


class IGovernanceModule(Protocol):
    """Governance 模块接口"""

    async def check_permission(
        self,
        agent_id: str,
        resource: str,
        required_level: PermissionLevel,
    ) -> bool:
        """检查权限"""
        ...

    async def grant_permission(
        self,
        agent_id: str,
        resource: str,
        level: PermissionLevel,
        conditions: Optional[Dict[str, Any]] = None,
    ) -> None:
        """授予权限"""
        ...

    async def revoke_permission(
        self,
        agent_id: str,
        resource: str,
    ) -> bool:
        """撤销权限"""
        ...

    async def audit(
        self,
        agent_id: str,
        action: AuditAction,
        resource: str,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
    ) -> str:
        """记录审计日志"""
        ...

    async def get_audit_logs(
        self,
        agent_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[AuditLog]:
        """获取审计日志"""
        ...

    async def check_rate_limit(
        self,
        agent_id: str,
        resource: str,
    ) -> bool:
        """检查速率限制"""
        ...
