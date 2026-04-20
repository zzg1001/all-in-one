"""
Reasoning 模块实现
"""

from typing import List, Optional, Dict, Any
import time

from portal.modules.base import (
    BaseModule,
    ModuleType,
    ModuleCategory,
    ReasoningModuleConfig,
)
from .interface import ReasoningStep, ReasoningResult, IReasoningModule


class ReasoningModule(BaseModule[ReasoningModuleConfig], IReasoningModule):
    """Reasoning 模块实现"""

    def __init__(self):
        super().__init__(ModuleType.REASONING, ModuleCategory.CORE)

    async def _on_initialize(self) -> None:
        """初始化推理引擎"""
        self._logger.info(f"Reasoning module initialized with style: {self._config.reasoning_style if self._config else 'default'}")

    async def reason(
        self,
        query: str,
        context: Optional[str] = None,
        style: Optional[str] = None
    ) -> ReasoningResult:
        """执行推理（Chain of Thought）"""
        start_time = time.time()

        reasoning_style = style or (self._config.reasoning_style if self._config else "step-by-step")

        # 生成推理步骤（基础实现，后续可对接 LLM）
        steps = await self._generate_reasoning_steps(query, context, reasoning_style)

        # 生成最终答案
        final_answer = await self._synthesize_answer(query, steps)

        result = ReasoningResult(
            query=query,
            steps=steps,
            final_answer=final_answer,
            reasoning_style=reasoning_style,
            total_steps=len(steps),
            confidence=self._calculate_confidence(steps),
        )

        latency_ms = (time.time() - start_time) * 1000
        self.update_metrics(True, latency_ms)

        return result

    async def analyze(
        self,
        content: str,
        analysis_type: str = "general"
    ) -> Dict[str, Any]:
        """分析内容"""
        start_time = time.time()

        analysis = {
            "content_length": len(content),
            "analysis_type": analysis_type,
            "key_points": [],
            "summary": "",
            "sentiment": "neutral",
        }

        # 基础分析（后续可对接 LLM 进行深度分析）
        if analysis_type == "general":
            analysis["summary"] = content[:200] + "..." if len(content) > 200 else content
        elif analysis_type == "sentiment":
            analysis["sentiment"] = self._basic_sentiment(content)
        elif analysis_type == "keywords":
            analysis["key_points"] = self._extract_keywords(content)

        latency_ms = (time.time() - start_time) * 1000
        self.update_metrics(True, latency_ms)

        return analysis

    async def validate(
        self,
        claim: str,
        evidence: List[str]
    ) -> Dict[str, Any]:
        """验证声明"""
        start_time = time.time()

        # 基础验证逻辑（后续可对接 LLM）
        validation = {
            "claim": claim,
            "evidence_count": len(evidence),
            "is_supported": False,
            "confidence": 0.0,
            "reasoning": "",
        }

        if evidence:
            # 简单的关键词匹配验证
            claim_words = set(claim.lower().split())
            support_count = 0
            for ev in evidence:
                ev_words = set(ev.lower().split())
                overlap = claim_words & ev_words
                if len(overlap) > len(claim_words) * 0.3:
                    support_count += 1

            validation["is_supported"] = support_count > len(evidence) * 0.5
            validation["confidence"] = support_count / len(evidence) if evidence else 0
            validation["reasoning"] = f"Found {support_count}/{len(evidence)} supporting evidence"

        latency_ms = (time.time() - start_time) * 1000
        self.update_metrics(True, latency_ms)

        return validation

    async def _generate_reasoning_steps(
        self,
        query: str,
        context: Optional[str],
        style: str
    ) -> List[ReasoningStep]:
        """生成推理步骤"""
        steps = []

        # 基础实现：生成模板化步骤
        # 后续可对接 LLM 生成真实的 CoT 步骤

        if style == "step-by-step":
            steps = [
                ReasoningStep(
                    step_number=1,
                    description="理解问题",
                    reasoning=f"分析用户查询: {query[:100]}",
                    confidence=0.9,
                ),
                ReasoningStep(
                    step_number=2,
                    description="收集信息",
                    reasoning="检索相关上下文和知识" + (f": {context[:100]}..." if context else ""),
                    confidence=0.85,
                ),
                ReasoningStep(
                    step_number=3,
                    description="推导结论",
                    reasoning="基于已有信息进行逻辑推导",
                    conclusion="需要进一步处理",
                    confidence=0.8,
                ),
            ]
        elif style == "tree-of-thought":
            steps = [
                ReasoningStep(
                    step_number=1,
                    description="分支探索",
                    reasoning="探索多个可能的解决路径",
                    confidence=0.85,
                ),
            ]

        return steps

    async def _synthesize_answer(self, query: str, steps: List[ReasoningStep]) -> str:
        """综合推理步骤生成答案"""
        if not steps:
            return "无法生成答案"

        # 基础实现
        return f"基于 {len(steps)} 步推理，针对问题「{query[:50]}」的分析已完成。"

    def _calculate_confidence(self, steps: List[ReasoningStep]) -> float:
        """计算总体置信度"""
        if not steps:
            return 0.0
        return sum(s.confidence for s in steps) / len(steps)

    def _basic_sentiment(self, content: str) -> str:
        """基础情感分析"""
        positive_words = ["好", "棒", "优秀", "喜欢", "满意", "感谢"]
        negative_words = ["差", "糟", "失望", "讨厌", "问题", "错误"]

        positive_count = sum(1 for w in positive_words if w in content)
        negative_count = sum(1 for w in negative_words if w in content)

        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        return "neutral"

    def _extract_keywords(self, content: str) -> List[str]:
        """提取关键词（基础实现）"""
        # 简单实现：返回较长的词
        words = content.split()
        keywords = [w for w in words if len(w) > 3]
        return keywords[:10]
