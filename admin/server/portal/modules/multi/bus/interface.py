"""
Agent Bus 模块接口定义
"""

from typing import Protocol, List, Optional, Dict, Any, Callable
from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class MessageType(str, Enum):
    """消息类型"""
    REQUEST = "request"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    EVENT = "event"


class MessageStatus(str, Enum):
    """消息状态"""
    PENDING = "pending"
    DELIVERED = "delivered"
    PROCESSED = "processed"
    FAILED = "failed"
    EXPIRED = "expired"


class AgentMessage(BaseModel):
    """Agent 消息"""
    id: str
    type: MessageType
    source_agent: str
    target_agent: Optional[str] = None  # None for broadcast
    topic: str = "default"
    payload: Dict[str, Any] = {}
    reply_to: Optional[str] = None  # 回复的消息ID
    status: MessageStatus = MessageStatus.PENDING
    created_at: datetime = datetime.now()
    delivered_at: Optional[datetime] = None
    ttl_seconds: int = 3600


class IBusModule(Protocol):
    """Agent Bus 模块接口"""

    async def send(
        self,
        source_agent: str,
        target_agent: str,
        topic: str,
        payload: Dict[str, Any],
        message_type: MessageType = MessageType.REQUEST,
    ) -> str:
        """发送消息，返回消息ID"""
        ...

    async def broadcast(
        self,
        source_agent: str,
        topic: str,
        payload: Dict[str, Any],
    ) -> str:
        """广播消息"""
        ...

    async def receive(
        self,
        agent_id: str,
        topic: Optional[str] = None,
        timeout: float = 30.0,
    ) -> Optional[AgentMessage]:
        """接收消息"""
        ...

    async def reply(
        self,
        original_message_id: str,
        payload: Dict[str, Any],
    ) -> str:
        """回复消息"""
        ...

    def subscribe(
        self,
        agent_id: str,
        topic: str,
        handler: Callable[[AgentMessage], Any],
    ) -> None:
        """订阅主题"""
        ...

    def unsubscribe(self, agent_id: str, topic: str) -> None:
        """取消订阅"""
        ...
