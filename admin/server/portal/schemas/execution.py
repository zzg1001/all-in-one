from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from datetime import datetime


# ============ Interaction Types ============

class InteractionOption(BaseModel):
    value: str
    label: str


class SkillInteraction(BaseModel):
    """Skill 的交互配置"""
    id: str
    type: str  # input, select, multiselect, confirm, upload, form
    label: str
    description: Optional[str] = None
    required: bool = True
    timing: str = "before"  # before=可预收集, during=需运行时
    depends_on: Optional[str] = None  # 依赖前序 Skill 的输出
    options: Optional[List[InteractionOption]] = None
    validation: Optional[Dict[str, Any]] = None


class InteractionRequest(BaseModel):
    """等待用户响应的交互请求"""
    interaction_id: str
    skill_id: Optional[int] = None
    skill_name: str
    step_index: int
    type: str
    label: str
    description: Optional[str] = None
    required: bool = True
    options: Optional[List[InteractionOption]] = None
    context: Optional[Dict[str, Any]] = None  # 前序步骤的输出


class InteractionResponse(BaseModel):
    """用户提交的交互响应"""
    interaction_id: str
    value: Any


# ============ Execution Types ============

class CompletedStep(BaseModel):
    """已完成的步骤"""
    step_index: int
    skill_name: str
    icon: Optional[str] = None
    status: str = "completed"  # completed, skipped
    result: Optional[Any] = None
    output: Optional[str] = None


class ExecutionStatus(BaseModel):
    """执行状态响应"""
    execution_id: str
    workflow_id: str
    workflow_name: Optional[str] = None
    status: str  # pending, running, paused, completed, failed
    current_step: int
    total_steps: int
    completed_steps: List[CompletedStep] = []
    pending_interaction: Optional[InteractionRequest] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class StartExecutionRequest(BaseModel):
    """启动执行请求"""
    pre_inputs: Optional[Dict[str, Any]] = None  # 预收集的交互输入


class ExecutionCreate(BaseModel):
    """创建执行实例"""
    workflow_id: str
    pre_inputs: Optional[Dict[str, Any]] = None


# ============ Workflow with Interactions ============

class WorkflowStepInfo(BaseModel):
    """工作流步骤信息（用于预检查）"""
    step_index: int
    skill_name: str
    icon: Optional[str] = None
    interactions: List[SkillInteraction] = []


class WorkflowPreCheck(BaseModel):
    """工作流预检查响应 - 返回所有需要预收集的交互"""
    workflow_id: str
    workflow_name: str
    total_steps: int
    steps: List[WorkflowStepInfo] = []
    before_interactions: List[InteractionRequest] = []  # timing=before 的交互
    has_during_interactions: bool = False  # 是否有 timing=during 的交互
