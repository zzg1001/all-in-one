"""
Registry 模块实现
Agent 服务注册中心
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import time
import asyncio

from portal.modules.base import (
    BaseModule,
    ModuleType,
    ModuleCategory,
    RegistryModuleConfig,
    ModuleEvent,
)
from .interface import ServiceInfo, ServiceStatus, IRegistryModule


class RegistryModule(BaseModule[RegistryModuleConfig], IRegistryModule):
    """Registry 模块实现"""

    def __init__(self):
        super().__init__(ModuleType.REGISTRY, ModuleCategory.MULTI)
        self._services: Dict[str, ServiceInfo] = {}
        self._health_check_task: Optional[asyncio.Task] = None

    async def _on_initialize(self) -> None:
        """初始化注册中心"""
        self._logger.info("Registry module initialized")

    async def _on_start(self) -> None:
        """启动健康检查任务"""
        self._health_check_task = asyncio.create_task(self._health_check_loop())

    async def _on_stop(self) -> None:
        """停止健康检查任务"""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

    async def _health_check_loop(self):
        """定期健康检查"""
        while True:
            try:
                interval = self._config.heartbeat_interval if self._config else 30
                await asyncio.sleep(interval)
                await self._check_all_services()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Health check error: {e}")

    async def _check_all_services(self):
        """检查所有服务健康状态"""
        ttl = self._config.service_ttl if self._config else 90
        now = datetime.now()

        for agent_id, service in list(self._services.items()):
            if service.last_heartbeat:
                elapsed = (now - service.last_heartbeat).total_seconds()
                if elapsed > ttl:
                    service.status = ServiceStatus.UNHEALTHY
                    self._logger.warning(f"Service {agent_id} is unhealthy (no heartbeat for {elapsed}s)")

                    # 发布不健康事件
                    await self._event_bus.publish(ModuleEvent(
                        event_type="service.unhealthy",
                        source_module=self._module_type.value,
                        payload={"agent_id": agent_id},
                    ))

    async def register(
        self,
        agent_id: str,
        name: str,
        capabilities: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """注册服务"""
        start_time = time.time()

        service = ServiceInfo(
            agent_id=agent_id,
            name=name,
            capabilities=capabilities,
            metadata=metadata or {},
            status=ServiceStatus.HEALTHY,
            registered_at=datetime.now(),
            last_heartbeat=datetime.now(),
        )

        self._services[agent_id] = service

        # 发布注册事件
        await self._event_bus.publish(ModuleEvent(
            event_type="service.registered",
            source_module=self._module_type.value,
            payload={"agent_id": agent_id, "name": name, "capabilities": capabilities},
        ))

        latency_ms = (time.time() - start_time) * 1000
        self.update_metrics(True, latency_ms)

        self._logger.info(f"Service registered: {agent_id} ({name})")
        return True

    async def deregister(self, agent_id: str) -> bool:
        """注销服务"""
        if agent_id not in self._services:
            return False

        del self._services[agent_id]

        # 发布注销事件
        await self._event_bus.publish(ModuleEvent(
            event_type="service.deregistered",
            source_module=self._module_type.value,
            payload={"agent_id": agent_id},
        ))

        self._logger.info(f"Service deregistered: {agent_id}")
        return True

    async def heartbeat(self, agent_id: str) -> bool:
        """发送心跳"""
        service = self._services.get(agent_id)
        if not service:
            return False

        service.last_heartbeat = datetime.now()
        service.status = ServiceStatus.HEALTHY

        return True

    async def discover(
        self,
        capability: Optional[str] = None,
        status: Optional[ServiceStatus] = None,
    ) -> List[ServiceInfo]:
        """服务发现"""
        start_time = time.time()

        services = list(self._services.values())

        if capability:
            services = [s for s in services if capability in s.capabilities]

        if status:
            services = [s for s in services if s.status == status]

        latency_ms = (time.time() - start_time) * 1000
        self.update_metrics(True, latency_ms)

        return services

    async def get_service(self, agent_id: str) -> Optional[ServiceInfo]:
        """获取服务信息"""
        return self._services.get(agent_id)

    async def health_check(self, agent_id: str) -> ServiceStatus:
        """健康检查"""
        service = self._services.get(agent_id)
        if not service:
            return ServiceStatus.UNKNOWN

        # 检查心跳时间
        if service.last_heartbeat:
            ttl = self._config.service_ttl if self._config else 90
            elapsed = (datetime.now() - service.last_heartbeat).total_seconds()
            if elapsed > ttl:
                service.status = ServiceStatus.UNHEALTHY

        return service.status
