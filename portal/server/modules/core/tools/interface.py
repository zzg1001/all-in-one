"""
Tools 模块接口定义
"""

from typing import Protocol, List, Optional, Dict, Any
from pydantic import BaseModel


class ToolDefinition(BaseModel):
    """工具定义"""
    name: str
    description: str
    category: str = "general"
    parameters: Dict[str, Any] = {}  # JSON Schema
    required_params: List[str] = []
    enabled: bool = True


class ToolExecutionResult(BaseModel):
    """工具执行结果"""
    tool_name: str
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    output_files: List[Dict[str, str]] = []


class IToolsModule(Protocol):
    """Tools 模块接口"""

    def register_tool(
        self,
        name: str,
        handler: Any,
        definition: ToolDefinition
    ) -> None:
        """注册工具"""
        ...

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """获取工具定义"""
        ...

    def list_tools(
        self,
        category: Optional[str] = None,
        enabled_only: bool = True
    ) -> List[ToolDefinition]:
        """列出工具"""
        ...

    async def execute(
        self,
        tool_name: str,
        params: Dict[str, Any]
    ) -> ToolExecutionResult:
        """执行工具"""
        ...

    async def discover(
        self,
        task_description: str
    ) -> List[ToolDefinition]:
        """根据任务描述发现相关工具"""
        ...
