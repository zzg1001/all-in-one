"""
Memory 模块实现
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from portal.modules.base import (
    BaseModule,
    ModuleType,
    ModuleCategory,
    MemoryModuleConfig,
)
from .interface import MemoryItem, IMemoryModule


class MemoryModule(BaseModule[MemoryModuleConfig], IMemoryModule):
    """Memory 模块实现"""

    def __init__(self):
        super().__init__(ModuleType.MEMORY, ModuleCategory.CORE)
        self._memories: Dict[str, MemoryItem] = {}  # 内存存储（后续可替换为数据库）

    async def _on_initialize(self) -> None:
        """初始化记忆存储"""
        self._logger.info(f"Memory module initialized with config: {self._config}")
        # 后续可以在这里初始化向量数据库连接等

    async def _on_stop(self) -> None:
        """停止时清理"""
        # 可以选择是否清除内存
        pass

    async def store(
        self,
        content: str,
        memory_type: str = "conversation",
        extra_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """存储记忆"""
        import time
        start_time = time.time()

        memory_id = str(uuid.uuid4())
        memory = MemoryItem(
            id=memory_id,
            content=content,
            memory_type=memory_type,
            extra_data=extra_data,
            created_at=datetime.now(),
        )

        # 如果启用向量存储，生成嵌入
        if self._config and self._config.vector_enabled:
            # TODO: 调用嵌入模型生成向量
            pass

        self._memories[memory_id] = memory

        # 检查是否超过最大历史记录
        if self._config and len(self._memories) > self._config.max_history * 2:
            await self._cleanup_old_memories()

        latency_ms = (time.time() - start_time) * 1000
        self.update_metrics(True, latency_ms)

        return memory_id

    async def retrieve(self, memory_id: str) -> Optional[MemoryItem]:
        """根据ID检索记忆"""
        return self._memories.get(memory_id)

    async def search(
        self,
        query: str,
        limit: int = 10,
        memory_type: Optional[str] = None
    ) -> List[MemoryItem]:
        """搜索相关记忆（基础实现使用关键词匹配）"""
        import time
        start_time = time.time()

        results = []
        query_lower = query.lower()

        for memory in self._memories.values():
            if memory_type and memory.memory_type != memory_type:
                continue
            if query_lower in memory.content.lower():
                results.append(memory)
                if len(results) >= limit:
                    break

        latency_ms = (time.time() - start_time) * 1000
        self.update_metrics(True, latency_ms)

        return results

    async def get_recent(
        self,
        limit: int = 20,
        memory_type: Optional[str] = None
    ) -> List[MemoryItem]:
        """获取最近的记忆"""
        memories = list(self._memories.values())

        if memory_type:
            memories = [m for m in memories if m.memory_type == memory_type]

        # 按创建时间排序
        memories.sort(key=lambda m: m.created_at, reverse=True)

        return memories[:limit]

    async def delete(self, memory_id: str) -> bool:
        """删除记忆"""
        if memory_id in self._memories:
            del self._memories[memory_id]
            return True
        return False

    async def clear(self, memory_type: Optional[str] = None) -> int:
        """清除记忆"""
        if memory_type is None:
            count = len(self._memories)
            self._memories.clear()
            return count

        to_delete = [
            mid for mid, m in self._memories.items()
            if m.memory_type == memory_type
        ]
        for mid in to_delete:
            del self._memories[mid]
        return len(to_delete)

    async def _cleanup_old_memories(self):
        """清理旧记忆，保留最近的记录"""
        if not self._config:
            return

        memories = list(self._memories.values())
        memories.sort(key=lambda m: m.created_at, reverse=True)

        # 保留最大历史数量
        keep_ids = {m.id for m in memories[:self._config.max_history]}
        to_delete = [mid for mid in self._memories if mid not in keep_ids]

        for mid in to_delete:
            del self._memories[mid]

        self._logger.info(f"Cleaned up {len(to_delete)} old memories")
