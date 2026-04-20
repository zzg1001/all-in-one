"""
Orchestrator 模块实现
多 Agent 编排器
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import time
import uuid
import asyncio

from portal.modules.base import (
    BaseModule,
    ModuleType,
    ModuleCategory,
    OrchestratorModuleConfig,
    ModuleEvent,
)
from .interface import Workflow, WorkflowNode, WorkflowResult, WorkflowStatus, IOrchestratorModule


class OrchestratorModule(BaseModule[OrchestratorModuleConfig], IOrchestratorModule):
    """Orchestrator 模块实现"""

    def __init__(self):
        super().__init__(ModuleType.ORCHESTRATOR, ModuleCategory.MULTI)
        self._workflows: Dict[str, Workflow] = {}
        self._running_tasks: Dict[str, asyncio.Task] = {}

    async def _on_initialize(self) -> None:
        """初始化编排器"""
        self._logger.info("Orchestrator module initialized")

    async def create_workflow(
        self,
        name: str,
        nodes: List[WorkflowNode],
        execution_mode: str = "sequential",
    ) -> Workflow:
        """创建工作流"""
        workflow_id = str(uuid.uuid4())

        workflow = Workflow(
            id=workflow_id,
            name=name,
            nodes=nodes,
            execution_mode=execution_mode,
            status=WorkflowStatus.PENDING,
            created_at=datetime.now(),
        )

        self._workflows[workflow_id] = workflow

        # 发布创建事件
        await self._event_bus.publish(ModuleEvent(
            event_type="workflow.created",
            source_module=self._module_type.value,
            payload={"workflow_id": workflow_id, "name": name},
        ))

        return workflow

    async def execute_workflow(
        self,
        workflow_id: str,
    ) -> WorkflowResult:
        """执行工作流"""
        start_time = time.time()

        workflow = self._workflows.get(workflow_id)
        if not workflow:
            return WorkflowResult(
                workflow_id=workflow_id,
                success=False,
                errors={"workflow": "工作流不存在"},
            )

        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.now()

        results: Dict[str, Any] = {}
        errors: Dict[str, str] = {}

        try:
            if workflow.execution_mode == "sequential":
                results, errors = await self._execute_sequential(workflow)
            elif workflow.execution_mode == "parallel":
                results, errors = await self._execute_parallel(workflow)
            elif workflow.execution_mode == "dag":
                results, errors = await self._execute_dag(workflow)
            else:
                errors["workflow"] = f"未知执行模式: {workflow.execution_mode}"

            workflow.status = WorkflowStatus.COMPLETED if not errors else WorkflowStatus.FAILED
            workflow.completed_at = datetime.now()

            # 发布完成事件
            await self._event_bus.publish(ModuleEvent(
                event_type="workflow.completed",
                source_module=self._module_type.value,
                payload={"workflow_id": workflow_id, "success": not errors},
            ))

        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            errors["workflow"] = str(e)

        execution_time_ms = (time.time() - start_time) * 1000
        self.update_metrics(not errors, execution_time_ms)

        return WorkflowResult(
            workflow_id=workflow_id,
            success=not errors,
            results=results,
            errors=errors,
            execution_time_ms=execution_time_ms,
        )

    async def _execute_sequential(self, workflow: Workflow) -> tuple[Dict[str, Any], Dict[str, str]]:
        """顺序执行"""
        results = {}
        errors = {}

        for node in workflow.nodes:
            if workflow.status == WorkflowStatus.PAUSED:
                break

            try:
                node.status = "running"
                result = await self._execute_node(node, results)
                node.result = result
                node.status = "completed"
                results[node.id] = result
            except Exception as e:
                node.status = "failed"
                errors[node.id] = str(e)
                break  # 顺序执行遇到错误就停止

        return results, errors

    async def _execute_parallel(self, workflow: Workflow) -> tuple[Dict[str, Any], Dict[str, str]]:
        """并行执行"""
        results = {}
        errors = {}

        max_concurrent = self._config.max_concurrent if self._config else 5
        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_with_semaphore(node):
            async with semaphore:
                node.status = "running"
                try:
                    result = await self._execute_node(node, {})
                    node.result = result
                    node.status = "completed"
                    return node.id, result, None
                except Exception as e:
                    node.status = "failed"
                    return node.id, None, str(e)

        tasks = [execute_with_semaphore(node) for node in workflow.nodes]
        completed = await asyncio.gather(*tasks)

        for node_id, result, error in completed:
            if error:
                errors[node_id] = error
            else:
                results[node_id] = result

        return results, errors

    async def _execute_dag(self, workflow: Workflow) -> tuple[Dict[str, Any], Dict[str, str]]:
        """DAG 执行（基于依赖关系）"""
        results = {}
        errors = {}
        completed_nodes = set()

        while len(completed_nodes) < len(workflow.nodes):
            if workflow.status == WorkflowStatus.PAUSED:
                break

            # 找到可执行的节点（依赖都已完成）
            ready_nodes = [
                node for node in workflow.nodes
                if node.id not in completed_nodes
                and all(dep in completed_nodes for dep in node.dependencies)
            ]

            if not ready_nodes:
                if len(completed_nodes) < len(workflow.nodes):
                    errors["workflow"] = "检测到循环依赖或无法执行的节点"
                break

            # 并行执行就绪节点
            max_concurrent = self._config.max_concurrent if self._config else 5
            batch = ready_nodes[:max_concurrent]

            async def execute_node(node):
                node.status = "running"
                try:
                    result = await self._execute_node(node, results)
                    node.result = result
                    node.status = "completed"
                    return node.id, result, None
                except Exception as e:
                    node.status = "failed"
                    return node.id, None, str(e)

            tasks = [execute_node(node) for node in batch]
            completed = await asyncio.gather(*tasks)

            for node_id, result, error in completed:
                completed_nodes.add(node_id)
                if error:
                    errors[node_id] = error
                else:
                    results[node_id] = result

        return results, errors

    async def _execute_node(self, node: WorkflowNode, context: Dict[str, Any]) -> Any:
        """执行单个节点"""
        # 基础实现：模拟执行
        # 后续可对接 Agent Bus 发送消息到目标 Agent

        await asyncio.sleep(0.1)  # 模拟执行时间

        return {
            "node_id": node.id,
            "agent_id": node.agent_id,
            "task": node.task,
            "executed_at": datetime.now().isoformat(),
        }

    async def pause_workflow(self, workflow_id: str) -> bool:
        """暂停工作流"""
        workflow = self._workflows.get(workflow_id)
        if not workflow or workflow.status != WorkflowStatus.RUNNING:
            return False

        workflow.status = WorkflowStatus.PAUSED
        return True

    async def resume_workflow(self, workflow_id: str) -> bool:
        """恢复工作流"""
        workflow = self._workflows.get(workflow_id)
        if not workflow or workflow.status != WorkflowStatus.PAUSED:
            return False

        workflow.status = WorkflowStatus.RUNNING
        return True

    async def cancel_workflow(self, workflow_id: str) -> bool:
        """取消工作流"""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            return False

        workflow.status = WorkflowStatus.FAILED

        # 取消正在运行的任务
        if workflow_id in self._running_tasks:
            self._running_tasks[workflow_id].cancel()
            del self._running_tasks[workflow_id]

        return True

    async def get_workflow_status(self, workflow_id: str) -> Optional[Workflow]:
        """获取工作流状态"""
        return self._workflows.get(workflow_id)
