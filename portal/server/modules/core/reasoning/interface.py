"""
Reasoning 模块接口定义
"""

from typing import Protocol, List, Optional, Dict, Any
from pydantic import BaseModel


class ReasoningStep(BaseModel):
    """推理步骤"""
    step_number: int
    description: str
    reasoning: str
    conclusion: Optional[str] = None
    confidence: float = 1.0


class ReasoningResult(BaseModel):
    """推理结果"""
    query: str
    steps: List[ReasoningStep]
    final_answer: str
    reasoning_style: str
    total_steps: int
    confidence: float


class IReasoningModule(Protocol):
    """Reasoning 模块接口"""

    async def reason(
        self,
        query: str,
        context: Optional[str] = None,
        style: Optional[str] = None
    ) -> ReasoningResult:
        """执行推理"""
        ...

    async def analyze(
        self,
        content: str,
        analysis_type: str = "general"
    ) -> Dict[str, Any]:
        """分析内容"""
        ...

    async def validate(
        self,
        claim: str,
        evidence: List[str]
    ) -> Dict[str, Any]:
        """验证声明"""
        ...
