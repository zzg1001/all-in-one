"""
Agent Bus 模块实现
Agent 通信总线
"""

from typing import List, Optional, Dict, Any, Callable
from datetime import datetime, timedelta
import time
import uuid
import asyncio
from collections import defaultdict

from modules.base import (
    BaseModule,
    ModuleType,
    ModuleCategory,
    BusModuleConfig,
    ModuleEvent,
)
from .interface import AgentMessage, MessageType, MessageStatus, IBusModule


class BusModule(BaseModule[BusModuleConfig], IBusModule):
    """Agent Bus 模块实现"""

    def __init__(self):
        super().__init__(ModuleType.BUS, ModuleCategory.MULTI)
        self._messages: Dict[str, AgentMessage] = {}
        self._queues: Dict[str, asyncio.Queue] = {}  # agent_id -> Queue
        self._subscriptions: Dict[str, Dict[str, List[Callable]]] = defaultdict(lambda: defaultdict(list))
        self._cleanup_task: Optional[asyncio.Task] = None

    async def _on_initialize(self) -> None:
        """初始化消息总线"""
        self._logger.info("Bus module initialized")

    async def _on_start(self) -> None:
        """启动清理任务"""
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_messages())

    async def _on_stop(self) -> None:
        """停止清理任务"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def _cleanup_expired_messages(self):
        """清理过期消息"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟检查一次
                now = datetime.now()
                ttl = self._config.message_ttl if self._config else 3600

                expired = []
                for msg_id, msg in self._messages.items():
                    age = (now - msg.created_at).total_seconds()
                    if age > ttl and msg.status == MessageStatus.PENDING:
                        msg.status = MessageStatus.EXPIRED
                        expired.append(msg_id)

                for msg_id in expired:
                    del self._messages[msg_id]

                if expired:
                    self._logger.info(f"Cleaned up {len(expired)} expired messages")

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Message cleanup error: {e}")

    def _get_queue(self, agent_id: str) -> asyncio.Queue:
        """获取或创建 Agent 的消息队列"""
        if agent_id not in self._queues:
            self._queues[agent_id] = asyncio.Queue()
        return self._queues[agent_id]

    async def send(
        self,
        source_agent: str,
        target_agent: str,
        topic: str,
        payload: Dict[str, Any],
        message_type: MessageType = MessageType.REQUEST,
    ) -> str:
        """发送消息"""
        start_time = time.time()

        message_id = str(uuid.uuid4())
        message = AgentMessage(
            id=message_id,
            type=message_type,
            source_agent=source_agent,
            target_agent=target_agent,
            topic=topic,
            payload=payload,
            ttl_seconds=self._config.message_ttl if self._config else 3600,
        )

        self._messages[message_id] = message

        # 放入目标 Agent 的队列
        queue = self._get_queue(target_agent)
        await queue.put(message)

        message.status = MessageStatus.DELIVERED
        message.delivered_at = datetime.now()

        # 触发订阅处理器
        await self._trigger_handlers(target_agent, topic, message)

        latency_ms = (time.time() - start_time) * 1000
        self.update_metrics(True, latency_ms)

        return message_id

    async def broadcast(
        self,
        source_agent: str,
        topic: str,
        payload: Dict[str, Any],
    ) -> str:
        """广播消息"""
        start_time = time.time()

        message_id = str(uuid.uuid4())
        message = AgentMessage(
            id=message_id,
            type=MessageType.BROADCAST,
            source_agent=source_agent,
            target_agent=None,
            topic=topic,
            payload=payload,
        )

        self._messages[message_id] = message

        # 发送给所有订阅该主题的 Agent
        for agent_id, topics in self._subscriptions.items():
            if topic in topics or "*" in topics:
                queue = self._get_queue(agent_id)
                await queue.put(message)
                await self._trigger_handlers(agent_id, topic, message)

        message.status = MessageStatus.DELIVERED
        message.delivered_at = datetime.now()

        latency_ms = (time.time() - start_time) * 1000
        self.update_metrics(True, latency_ms)

        return message_id

    async def receive(
        self,
        agent_id: str,
        topic: Optional[str] = None,
        timeout: float = 30.0,
    ) -> Optional[AgentMessage]:
        """接收消息"""
        queue = self._get_queue(agent_id)

        try:
            message = await asyncio.wait_for(queue.get(), timeout=timeout)

            # 过滤主题
            if topic and message.topic != topic:
                # 放回队列（简化处理）
                await queue.put(message)
                return None

            message.status = MessageStatus.PROCESSED
            return message

        except asyncio.TimeoutError:
            return None

    async def reply(
        self,
        original_message_id: str,
        payload: Dict[str, Any],
    ) -> str:
        """回复消息"""
        original = self._messages.get(original_message_id)
        if not original:
            raise ValueError(f"原始消息不存在: {original_message_id}")

        return await self.send(
            source_agent=original.target_agent or "system",
            target_agent=original.source_agent,
            topic=original.topic,
            payload=payload,
            message_type=MessageType.RESPONSE,
        )

    def subscribe(
        self,
        agent_id: str,
        topic: str,
        handler: Callable[[AgentMessage], Any],
    ) -> None:
        """订阅主题"""
        self._subscriptions[agent_id][topic].append(handler)
        self._logger.debug(f"Agent {agent_id} subscribed to topic: {topic}")

    def unsubscribe(self, agent_id: str, topic: str) -> None:
        """取消订阅"""
        if agent_id in self._subscriptions and topic in self._subscriptions[agent_id]:
            del self._subscriptions[agent_id][topic]

    async def _trigger_handlers(self, agent_id: str, topic: str, message: AgentMessage):
        """触发订阅处理器"""
        handlers = self._subscriptions.get(agent_id, {}).get(topic, [])
        handlers.extend(self._subscriptions.get(agent_id, {}).get("*", []))

        for handler in handlers:
            try:
                result = handler(message)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                self._logger.error(f"Handler error for {agent_id}/{topic}: {e}")
