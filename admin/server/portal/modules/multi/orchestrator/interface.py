"""
Orchestrator 模块接口定义
"""

from typing import Protocol, List, Optional, Dict, Any, Callable
from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class WorkflowStatus(str, Enum):
    """工作流状态"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowNode(BaseModel):
    """工作流节点"""
    id: str
    agent_id: str
    task: str
    params: Dict[str, Any] = {}
    dependencies: List[str] = []
    status: str = "pending"
    result: Optional[Any] = None


class Workflow(BaseModel):
    """工作流定义"""
    id: str
    name: str
    description: str = ""
    nodes: List[WorkflowNode] = []
    execution_mode: str = "sequential"  # sequential, parallel, dag
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_at: datetime = datetime.now()
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class WorkflowResult(BaseModel):
    """工作流执行结果"""
    workflow_id: str
    success: bool
    results: Dict[str, Any] = {}  # node_id -> result
    errors: Dict[str, str] = {}  # node_id -> error
    execution_time_ms: float = 0.0


class IOrchestratorModule(Protocol):
    """Orchestrator 模块接口"""

    async def create_workflow(
        self,
        name: str,
        nodes: List[WorkflowNode],
        execution_mode: str = "sequential",
    ) -> Workflow:
        """创建工作流"""
        ...

    async def execute_workflow(
        self,
        workflow_id: str,
    ) -> WorkflowResult:
        """执行工作流"""
        ...

    async def pause_workflow(self, workflow_id: str) -> bool:
        """暂停工作流"""
        ...

    async def resume_workflow(self, workflow_id: str) -> bool:
        """恢复工作流"""
        ...

    async def cancel_workflow(self, workflow_id: str) -> bool:
        """取消工作流"""
        ...

    async def get_workflow_status(self, workflow_id: str) -> Optional[Workflow]:
        """获取工作流状态"""
        ...
