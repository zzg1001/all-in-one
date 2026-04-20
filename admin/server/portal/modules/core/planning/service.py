"""
Planning 模块实现
"""

from typing import List, Optional, Dict, Any
import time
import uuid

from portal.modules.base import (
    BaseModule,
    ModuleType,
    ModuleCategory,
    PlanningModuleConfig,
)
from .interface import PlanTask, ExecutionPlan, TaskStatus, IPlanningModule


class PlanningModule(BaseModule[PlanningModuleConfig], IPlanningModule):
    """Planning 模块实现"""

    def __init__(self):
        super().__init__(ModuleType.PLANNING, ModuleCategory.CORE)
        self._plans: Dict[str, ExecutionPlan] = {}

    async def _on_initialize(self) -> None:
        """初始化规划引擎"""
        self._logger.info(f"Planning module initialized with strategy: {self._config.planning_strategy if self._config else 'default'}")

    async def create_plan(
        self,
        goal: str,
        context: Optional[str] = None,
        available_skills: Optional[List[str]] = None,
        available_tools: Optional[List[str]] = None,
    ) -> ExecutionPlan:
        """创建执行计划"""
        start_time = time.time()

        plan_id = str(uuid.uuid4())

        # 分解目标为任务
        tasks = await self._analyze_goal(goal, context, available_skills, available_tools)

        # 确定执行策略
        strategy = self._determine_strategy(tasks)

        plan = ExecutionPlan(
            id=plan_id,
            goal=goal,
            tasks=tasks,
            strategy=strategy,
            total_tasks=len(tasks),
            completed_tasks=0,
            status="pending",
        )

        self._plans[plan_id] = plan

        latency_ms = (time.time() - start_time) * 1000
        self.update_metrics(True, latency_ms)

        return plan

    async def decompose_task(
        self,
        task: str,
        max_depth: int = 3
    ) -> List[PlanTask]:
        """分解任务为子任务"""
        start_time = time.time()

        # 基础实现：简单分解
        # 后续可对接 LLM 进行智能分解

        subtasks = []
        task_id_base = str(uuid.uuid4())[:8]

        # 模板化分解
        subtasks = [
            PlanTask(
                id=f"{task_id_base}-1",
                name="分析需求",
                description=f"分析任务: {task}",
                order=1,
            ),
            PlanTask(
                id=f"{task_id_base}-2",
                name="准备资源",
                description="收集必要的资源和信息",
                dependencies=[f"{task_id_base}-1"],
                order=2,
            ),
            PlanTask(
                id=f"{task_id_base}-3",
                name="执行任务",
                description="执行核心任务",
                dependencies=[f"{task_id_base}-2"],
                order=3,
            ),
            PlanTask(
                id=f"{task_id_base}-4",
                name="验证结果",
                description="验证执行结果",
                dependencies=[f"{task_id_base}-3"],
                order=4,
            ),
        ]

        latency_ms = (time.time() - start_time) * 1000
        self.update_metrics(True, latency_ms)

        return subtasks

    async def replan(
        self,
        plan: ExecutionPlan,
        failed_task_id: str,
        error: str
    ) -> ExecutionPlan:
        """根据失败重新规划"""
        start_time = time.time()

        if not self._config or not self._config.enable_replanning:
            # 不允许重新规划，直接标记计划失败
            plan.status = "failed"
            return plan

        # 找到失败的任务
        failed_task = None
        for task in plan.tasks:
            if task.id == failed_task_id:
                failed_task = task
                task.status = TaskStatus.FAILED
                task.error = error
                break

        if not failed_task:
            return plan

        # 生成替代方案
        alternative_tasks = await self._generate_alternatives(failed_task, error)

        if alternative_tasks:
            # 插入替代任务
            insert_index = plan.tasks.index(failed_task) + 1
            for i, alt_task in enumerate(alternative_tasks):
                alt_task.order = failed_task.order + i + 1
                plan.tasks.insert(insert_index + i, alt_task)

            # 更新后续任务的依赖
            for task in plan.tasks[insert_index + len(alternative_tasks):]:
                if failed_task_id in task.dependencies:
                    task.dependencies.remove(failed_task_id)
                    task.dependencies.append(alternative_tasks[-1].id)

            plan.total_tasks = len([t for t in plan.tasks if t.status != TaskStatus.FAILED])
            plan.status = "replanned"
        else:
            plan.status = "failed"

        latency_ms = (time.time() - start_time) * 1000
        self.update_metrics(True, latency_ms)

        return plan

    async def get_next_task(
        self,
        plan: ExecutionPlan
    ) -> Optional[PlanTask]:
        """获取下一个可执行任务"""
        completed_ids = {
            t.id for t in plan.tasks
            if t.status in [TaskStatus.COMPLETED, TaskStatus.SKIPPED]
        }

        for task in plan.tasks:
            if task.status == TaskStatus.PENDING:
                # 检查依赖是否都已完成
                if all(dep_id in completed_ids for dep_id in task.dependencies):
                    return task

        return None

    async def _analyze_goal(
        self,
        goal: str,
        context: Optional[str],
        available_skills: Optional[List[str]],
        available_tools: Optional[List[str]],
    ) -> List[PlanTask]:
        """分析目标并生成任务列表"""
        tasks = []
        task_id_base = str(uuid.uuid4())[:8]

        # 基础实现：根据目标关键词匹配技能/工具
        # 后续可对接 LLM 进行智能规划

        # 生成默认任务流程
        task_order = 0

        # 分析任务
        task_order += 1
        tasks.append(PlanTask(
            id=f"{task_id_base}-analyze",
            name="分析目标",
            description=f"分析用户目标: {goal[:100]}",
            order=task_order,
        ))

        # 根据可用技能添加任务
        if available_skills:
            for skill_id in available_skills[:3]:  # 最多使用3个技能
                task_order += 1
                tasks.append(PlanTask(
                    id=f"{task_id_base}-skill-{task_order}",
                    name=f"执行技能",
                    description=f"使用技能 {skill_id}",
                    skill_id=skill_id,
                    dependencies=[tasks[-1].id],
                    order=task_order,
                ))

        # 汇总任务
        task_order += 1
        tasks.append(PlanTask(
            id=f"{task_id_base}-summarize",
            name="汇总结果",
            description="整合所有结果并生成报告",
            dependencies=[tasks[-1].id] if len(tasks) > 1 else [],
            order=task_order,
        ))

        return tasks

    def _determine_strategy(self, tasks: List[PlanTask]) -> str:
        """确定执行策略"""
        # 检查是否有依赖关系
        has_dependencies = any(t.dependencies for t in tasks)

        if not has_dependencies:
            return "parallel"

        # 检查是否是简单的线性依赖
        is_linear = True
        for i, task in enumerate(tasks[1:], 1):
            if task.dependencies != [tasks[i-1].id]:
                is_linear = False
                break

        if is_linear:
            return "sequential"

        return "dag"

    async def _generate_alternatives(
        self,
        failed_task: PlanTask,
        error: str
    ) -> List[PlanTask]:
        """为失败任务生成替代方案"""
        # 基础实现：生成一个重试任务
        # 后续可对接 LLM 生成智能替代方案

        alt_id = str(uuid.uuid4())[:8]

        return [
            PlanTask(
                id=f"{alt_id}-retry",
                name=f"重试: {failed_task.name}",
                description=f"尝试替代方案执行: {failed_task.description}",
                skill_id=failed_task.skill_id,
                tool_name=failed_task.tool_name,
                params=failed_task.params,
                dependencies=failed_task.dependencies,
            )
        ]
