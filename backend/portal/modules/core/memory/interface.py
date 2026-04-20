"""
Memory 模块接口定义
"""

from typing import Protocol, List, Optional, Dict, Any
from datetime import datetime


class MemoryItem:
    """记忆项"""
    def __init__(
        self,
        id: str,
        content: str,
        memory_type: str,
        extra_data: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None,
        created_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
    ):
        self.id = id
        self.content = content
        self.memory_type = memory_type
        self.extra_data = extra_data or {}
        self.embedding = embedding
        self.created_at = created_at or datetime.now()
        self.expires_at = expires_at


class IMemoryModule(Protocol):
    """Memory 模块接口"""

    async def store(self, content: str, memory_type: str = "conversation", extra_data: Optional[Dict[str, Any]] = None) -> str:
        """存储记忆，返回记忆ID"""
        ...

    async def retrieve(self, memory_id: str) -> Optional[MemoryItem]:
        """根据ID检索记忆"""
        ...

    async def search(self, query: str, limit: int = 10, memory_type: Optional[str] = None) -> List[MemoryItem]:
        """搜索相关记忆"""
        ...

    async def get_recent(self, limit: int = 20, memory_type: Optional[str] = None) -> List[MemoryItem]:
        """获取最近的记忆"""
        ...

    async def delete(self, memory_id: str) -> bool:
        """删除记忆"""
        ...

    async def clear(self, memory_type: Optional[str] = None) -> int:
        """清除记忆，返回清除数量"""
        ...
