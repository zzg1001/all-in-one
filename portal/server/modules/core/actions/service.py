"""
Actions 模块实现
"""

from typing import List, Optional, Dict, Any, Callable
from datetime import datetime
import time
import uuid
import asyncio
from collections import deque

from modules.base import (
    BaseModule,
    ModuleType,
    ModuleCategory,
    ActionsModuleConfig,
    ModuleEvent,
)
from .interface import Action, ActionResult, ActionStatus, ActionType, IActionsModule


class ActionsModule(BaseModule[ActionsModuleConfig], IActionsModule):
    """Actions 模块实现"""

    def __init__(self):
        super().__init__(ModuleType.ACTIONS, ModuleCategory.CORE)
        self._queue: deque[Action] = deque()
        self._actions: Dict[str, Action] = {}  # 所有动作的记录
        self._handlers: Dict[ActionType, Callable] = {}

    async def _on_initialize(self) -> None:
        """初始化动作队列"""
        self._logger.info(f"Actions module initialized with queue size: {self._config.max_queue_size if self._config else 100}")

    def register_handler(self, action_type: ActionType, handler: Callable):
        """注册动作处理器"""
        self._handlers[action_type] = handler
        self._logger.info(f"Registered handler for action type: {action_type.value}")

    async def enqueue(
        self,
        action_type: ActionType,
        name: str,
        params: Dict[str, Any],
        priority: int = 0,
    ) -> str:
        """添加动作到队列"""
        # 检查队列是否已满
        max_size = self._config.max_queue_size if self._config else 100
        if len(self._queue) >= max_size:
            raise RuntimeError(f"动作队列已满 (最大 {max_size})")

        action_id = str(uuid.uuid4())
        action = Action(
            id=action_id,
            type=action_type,
            name=name,
            params=params,
            priority=priority,
            max_retries=self._config.retry_count if self._config else 3,
            timeout_seconds=self._config.action_timeout if self._config else 60,
            created_at=datetime.now(),
        )

        self._actions[action_id] = action

        # 按优先级插入队列
        if priority > 0:
            # 找到合适的位置
            inserted = False
            for i, existing in enumerate(self._queue):
                if priority > existing.priority:
                    self._queue.insert(i, action)
                    inserted = True
                    break
            if not inserted:
                self._queue.append(action)
        else:
            self._queue.append(action)

        # 发布事件
        await self._event_bus.publish(ModuleEvent(
            event_type="action.queued",
            source_module=self._module_type.value,
            payload={"action_id": action_id, "type": action_type.value, "name": name},
        ))

        return action_id

    async def execute_next(self) -> Optional[ActionResult]:
        """执行队列中的下一个动作"""
        if not self._queue:
            return None

        action = self._queue.popleft()
        return await self._execute_action(action)

    async def _execute_action(self, action: Action) -> ActionResult:
        """执行单个动作"""
        start_time = time.time()

        action.status = ActionStatus.RUNNING
        action.started_at = datetime.now()

        # 发布开始事件
        await self._event_bus.publish(ModuleEvent(
            event_type="action.started",
            source_module=self._module_type.value,
            payload={"action_id": action.id},
        ))

        try:
            # 获取处理器
            handler = self._handlers.get(action.type)

            if handler:
                # 设置超时
                try:
                    if asyncio.iscoroutinefunction(handler):
                        result = await asyncio.wait_for(
                            handler(action.name, action.params),
                            timeout=action.timeout_seconds
                        )
                    else:
                        result = await asyncio.wait_for(
                            asyncio.to_thread(handler, action.name, action.params),
                            timeout=action.timeout_seconds
                        )
                except asyncio.TimeoutError:
                    action.status = ActionStatus.TIMEOUT
                    action.error = f"执行超时 ({action.timeout_seconds}s)"
                    action.completed_at = datetime.now()

                    execution_time_ms = (time.time() - start_time) * 1000
                    self.update_metrics(False, execution_time_ms)

                    # 检查是否需要重试
                    if action.retry_count < action.max_retries:
                        action.retry_count += 1
                        action.status = ActionStatus.QUEUED
                        self._queue.appendleft(action)

                    return ActionResult(
                        action_id=action.id,
                        success=False,
                        error=action.error,
                        execution_time_ms=execution_time_ms,
                        retries=action.retry_count,
                    )
            else:
                # 没有处理器，模拟执行
                result = {
                    "message": f"动作 {action.name} 已执行",
                    "type": action.type.value,
                    "params": action.params,
                }

            action.status = ActionStatus.COMPLETED
            action.result = result
            action.completed_at = datetime.now()

            execution_time_ms = (time.time() - start_time) * 1000
            self.update_metrics(True, execution_time_ms)

            # 发布完成事件
            await self._event_bus.publish(ModuleEvent(
                event_type="action.completed",
                source_module=self._module_type.value,
                payload={"action_id": action.id, "success": True},
            ))

            return ActionResult(
                action_id=action.id,
                success=True,
                result=result,
                execution_time_ms=execution_time_ms,
                retries=action.retry_count,
            )

        except Exception as e:
            action.status = ActionStatus.FAILED
            action.error = str(e)
            action.completed_at = datetime.now()

            execution_time_ms = (time.time() - start_time) * 1000
            self.update_metrics(False, execution_time_ms)

            # 检查是否需要重试
            if action.retry_count < action.max_retries:
                action.retry_count += 1
                action.status = ActionStatus.QUEUED
                self._queue.appendleft(action)
                self._logger.warning(f"Action {action.id} failed, retrying ({action.retry_count}/{action.max_retries})")

            # 发布失败事件
            await self._event_bus.publish(ModuleEvent(
                event_type="action.failed",
                source_module=self._module_type.value,
                payload={"action_id": action.id, "error": str(e)},
            ))

            return ActionResult(
                action_id=action.id,
                success=False,
                error=str(e),
                execution_time_ms=execution_time_ms,
                retries=action.retry_count,
            )

    async def get_status(self, action_id: str) -> Optional[Action]:
        """获取动作状态"""
        return self._actions.get(action_id)

    async def cancel(self, action_id: str) -> bool:
        """取消动作"""
        action = self._actions.get(action_id)
        if not action:
            return False

        if action.status == ActionStatus.QUEUED:
            # 从队列中移除
            try:
                self._queue.remove(action)
            except ValueError:
                pass

            action.status = ActionStatus.CANCELLED
            action.completed_at = datetime.now()

            await self._event_bus.publish(ModuleEvent(
                event_type="action.cancelled",
                source_module=self._module_type.value,
                payload={"action_id": action_id},
            ))

            return True

        return False

    def get_queue_length(self) -> int:
        """获取队列长度"""
        return len(self._queue)

    async def clear_queue(self) -> int:
        """清空队列"""
        count = len(self._queue)

        for action in self._queue:
            action.status = ActionStatus.CANCELLED
            action.completed_at = datetime.now()

        self._queue.clear()

        return count

    async def execute_all(self) -> List[ActionResult]:
        """执行队列中的所有动作"""
        results = []

        while self._queue:
            result = await self.execute_next()
            if result:
                results.append(result)

        return results
