"""
Governance 模块实现
治理和权限管理
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import time
import uuid
from collections import defaultdict

from modules.base import (
    BaseModule,
    ModuleType,
    ModuleCategory,
    GovernanceModuleConfig,
    ModuleEvent,
)
from .interface import (
    Permission,
    AuditLog,
    PermissionLevel,
    AuditAction,
    IGovernanceModule,
)


class GovernanceModule(BaseModule[GovernanceModuleConfig], IGovernanceModule):
    """Governance 模块实现"""

    def __init__(self):
        super().__init__(ModuleType.GOVERNANCE, ModuleCategory.MULTI)
        self._permissions: Dict[str, Dict[str, Permission]] = defaultdict(dict)  # agent_id -> {resource -> permission}
        self._audit_logs: List[AuditLog] = []
        self._rate_counters: Dict[str, Dict[str, List[datetime]]] = defaultdict(lambda: defaultdict(list))

    async def _on_initialize(self) -> None:
        """初始化治理模块"""
        self._logger.info("Governance module initialized")

    async def check_permission(
        self,
        agent_id: str,
        resource: str,
        required_level: PermissionLevel,
    ) -> bool:
        """检查权限"""
        start_time = time.time()

        # 权限级别优先级
        level_priority = {
            PermissionLevel.NONE: 0,
            PermissionLevel.READ: 1,
            PermissionLevel.WRITE: 2,
            PermissionLevel.EXECUTE: 3,
            PermissionLevel.ADMIN: 4,
        }

        permission = self._permissions.get(agent_id, {}).get(resource)

        if not permission:
            # 检查通配符权限
            permission = self._permissions.get(agent_id, {}).get("*")

        if not permission:
            latency_ms = (time.time() - start_time) * 1000
            self.update_metrics(True, latency_ms)
            return False

        has_permission = level_priority[permission.level] >= level_priority[required_level]

        latency_ms = (time.time() - start_time) * 1000
        self.update_metrics(True, latency_ms)

        return has_permission

    async def grant_permission(
        self,
        agent_id: str,
        resource: str,
        level: PermissionLevel,
        conditions: Optional[Dict[str, Any]] = None,
    ) -> None:
        """授予权限"""
        permission = Permission(
            resource=resource,
            level=level,
            conditions=conditions or {},
        )

        self._permissions[agent_id][resource] = permission

        # 记录审计日志
        await self.audit(
            agent_id="system",
            action=AuditAction.CREATE,
            resource=f"permission:{agent_id}:{resource}",
            details={"level": level.value},
        )

        self._logger.info(f"Granted {level.value} permission on {resource} to {agent_id}")

    async def revoke_permission(
        self,
        agent_id: str,
        resource: str,
    ) -> bool:
        """撤销权限"""
        if agent_id in self._permissions and resource in self._permissions[agent_id]:
            del self._permissions[agent_id][resource]

            # 记录审计日志
            await self.audit(
                agent_id="system",
                action=AuditAction.DELETE,
                resource=f"permission:{agent_id}:{resource}",
            )

            return True

        return False

    async def audit(
        self,
        agent_id: str,
        action: AuditAction,
        resource: str,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
    ) -> str:
        """记录审计日志"""
        if not self._config or not self._config.enable_audit:
            return ""

        log_id = str(uuid.uuid4())
        log = AuditLog(
            id=log_id,
            timestamp=datetime.now(),
            agent_id=agent_id,
            action=action,
            resource=resource,
            details=details or {},
            success=success,
        )

        self._audit_logs.append(log)

        # 限制日志数量
        max_logs = 10000
        if len(self._audit_logs) > max_logs:
            self._audit_logs = self._audit_logs[-max_logs:]

        # 发布审计事件
        await self._event_bus.publish(ModuleEvent(
            event_type="audit.logged",
            source_module=self._module_type.value,
            payload={
                "log_id": log_id,
                "agent_id": agent_id,
                "action": action.value,
                "resource": resource,
            },
        ))

        return log_id

    async def get_audit_logs(
        self,
        agent_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[AuditLog]:
        """获取审计日志"""
        logs = self._audit_logs.copy()

        # 过滤
        if agent_id:
            logs = [l for l in logs if l.agent_id == agent_id]
        if action:
            logs = [l for l in logs if l.action == action]
        if start_time:
            logs = [l for l in logs if l.timestamp >= start_time]
        if end_time:
            logs = [l for l in logs if l.timestamp <= end_time]

        # 按时间倒序
        logs.sort(key=lambda l: l.timestamp, reverse=True)

        return logs[:limit]

    async def check_rate_limit(
        self,
        agent_id: str,
        resource: str,
    ) -> bool:
        """检查速率限制"""
        if not self._config:
            return True

        rate_limit = self._config.rate_limit
        window = timedelta(minutes=1)
        now = datetime.now()

        # 清理过期的计数
        self._rate_counters[agent_id][resource] = [
            ts for ts in self._rate_counters[agent_id][resource]
            if now - ts < window
        ]

        # 检查是否超限
        if len(self._rate_counters[agent_id][resource]) >= rate_limit:
            await self.audit(
                agent_id=agent_id,
                action=AuditAction.EXECUTE,
                resource=resource,
                details={"reason": "rate_limit_exceeded"},
                success=False,
            )
            return False

        # 记录本次请求
        self._rate_counters[agent_id][resource].append(now)
        return True

    async def require_approval(
        self,
        agent_id: str,
        action: str,
    ) -> bool:
        """检查是否需要审批"""
        if not self._config:
            return False
        return action in self._config.require_approval

    def get_agent_permissions(self, agent_id: str) -> List[Permission]:
        """获取 Agent 的所有权限"""
        return list(self._permissions.get(agent_id, {}).values())
