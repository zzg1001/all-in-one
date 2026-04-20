"""
Actions 模块接口定义
"""

from typing import Protocol, List, Optional, Dict, Any, Callable
from pydantic import BaseModel
from enum import Enum
from datetime import datetime


class ActionStatus(str, Enum):
    """动作状态"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ActionType(str, Enum):
    """动作类型"""
    TOOL_CALL = "tool_call"
    SKILL_EXEC = "skill_exec"
    API_CALL = "api_call"
    CUSTOM = "custom"


class Action(BaseModel):
    """动作定义"""
    id: str
    type: ActionType
    name: str
    params: Dict[str, Any] = {}
    status: ActionStatus = ActionStatus.QUEUED
    priority: int = 0  # 优先级，数字越大优先级越高
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: int = 60
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = datetime.now()
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ActionResult(BaseModel):
    """动作执行结果"""
    action_id: str
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    retries: int = 0


class IActionsModule(Protocol):
    """Actions 模块接口"""

    async def enqueue(
        self,
        action_type: ActionType,
        name: str,
        params: Dict[str, Any],
        priority: int = 0,
    ) -> str:
        """添加动作到队列，返回动作ID"""
        ...

    async def execute_next(self) -> Optional[ActionResult]:
        """执行队列中的下一个动作"""
        ...

    async def get_status(self, action_id: str) -> Optional[Action]:
        """获取动作状态"""
        ...

    async def cancel(self, action_id: str) -> bool:
        """取消动作"""
        ...

    def get_queue_length(self) -> int:
        """获取队列长度"""
        ...

    async def clear_queue(self) -> int:
        """清空队列，返回清除的动作数"""
        ...
