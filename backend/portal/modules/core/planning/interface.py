"""
Planning 模块接口定义
"""

from typing import Protocol, List, Optional, Dict, Any
from pydantic import BaseModel
from enum import Enum


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PlanTask(BaseModel):
    """计划任务"""
    id: str
    name: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[str] = []  # 依赖的任务ID
    skill_id: Optional[str] = None  # 关联的技能ID
    tool_name: Optional[str] = None  # 使用的工具
    params: Dict[str, Any] = {}
    result: Optional[Any] = None
    error: Optional[str] = None
    order: int = 0


class ExecutionPlan(BaseModel):
    """执行计划"""
    id: str
    goal: str
    tasks: List[PlanTask]
    strategy: str = "sequential"  # sequential, parallel, dag
    total_tasks: int
    completed_tasks: int = 0
    status: str = "pending"


class IPlanningModule(Protocol):
    """Planning 模块接口"""

    async def create_plan(
        self,
        goal: str,
        context: Optional[str] = None,
        available_skills: Optional[List[str]] = None,
        available_tools: Optional[List[str]] = None,
    ) -> ExecutionPlan:
        """创建执行计划"""
        ...

    async def decompose_task(
        self,
        task: str,
        max_depth: int = 3
    ) -> List[PlanTask]:
        """分解任务为子任务"""
        ...

    async def replan(
        self,
        plan: ExecutionPlan,
        failed_task_id: str,
        error: str
    ) -> ExecutionPlan:
        """根据失败重新规划"""
        ...

    async def get_next_task(
        self,
        plan: ExecutionPlan
    ) -> Optional[PlanTask]:
        """获取下一个可执行任务"""
        ...
