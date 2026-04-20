"""
Tools 模块实现
"""

from typing import List, Optional, Dict, Any, Callable
import time
import asyncio

from portal.modules.base import (
    BaseModule,
    ModuleType,
    ModuleCategory,
    ToolsModuleConfig,
)
from .interface import ToolDefinition, ToolExecutionResult, IToolsModule


class ToolsModule(BaseModule[ToolsModuleConfig], IToolsModule):
    """Tools 模块实现"""

    def __init__(self):
        super().__init__(ModuleType.TOOLS, ModuleCategory.CORE)
        self._tools: Dict[str, ToolDefinition] = {}
        self._handlers: Dict[str, Callable] = {}

    async def _on_initialize(self) -> None:
        """初始化工具注册表"""
        self._logger.info("Tools module initialized")
        # 注册默认工具
        await self._register_default_tools()

    async def _register_default_tools(self):
        """注册默认工具"""
        default_tools = [
            ToolDefinition(
                name="read",
                description="读取文件内容",
                category="file",
                parameters={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "文件路径"},
                    },
                },
                required_params=["file_path"],
            ),
            ToolDefinition(
                name="write",
                description="写入文件内容",
                category="file",
                parameters={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "文件路径"},
                        "content": {"type": "string", "description": "文件内容"},
                    },
                },
                required_params=["file_path", "content"],
            ),
            ToolDefinition(
                name="bash",
                description="执行 Shell 命令",
                category="system",
                parameters={
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "要执行的命令"},
                    },
                },
                required_params=["command"],
            ),
            ToolDefinition(
                name="code_exec",
                description="执行代码",
                category="code",
                parameters={
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "代码内容"},
                        "language": {"type": "string", "description": "编程语言"},
                    },
                },
                required_params=["code"],
            ),
            ToolDefinition(
                name="web_search",
                description="网络搜索",
                category="web",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "搜索关键词"},
                    },
                },
                required_params=["query"],
            ),
            ToolDefinition(
                name="web_fetch",
                description="获取网页内容",
                category="web",
                parameters={
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "网页URL"},
                    },
                },
                required_params=["url"],
            ),
        ]

        for tool in default_tools:
            self._tools[tool.name] = tool

    def register_tool(
        self,
        name: str,
        handler: Callable,
        definition: ToolDefinition
    ) -> None:
        """注册工具"""
        self._tools[name] = definition
        self._handlers[name] = handler
        self._logger.info(f"Registered tool: {name}")

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """获取工具定义"""
        return self._tools.get(name)

    def list_tools(
        self,
        category: Optional[str] = None,
        enabled_only: bool = True
    ) -> List[ToolDefinition]:
        """列出工具"""
        tools = list(self._tools.values())

        if category:
            tools = [t for t in tools if t.category == category]

        if enabled_only:
            tools = [t for t in tools if t.enabled]

        # 过滤只允许的工具
        if self._config and self._config.allowed_tools:
            tools = [t for t in tools if t.name in self._config.allowed_tools]

        return tools

    async def execute(
        self,
        tool_name: str,
        params: Dict[str, Any]
    ) -> ToolExecutionResult:
        """执行工具"""
        start_time = time.time()

        tool = self._tools.get(tool_name)
        if not tool:
            return ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                error=f"工具 {tool_name} 不存在",
            )

        if not tool.enabled:
            return ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                error=f"工具 {tool_name} 未启用",
            )

        # 检查是否允许使用
        if self._config and self._config.allowed_tools:
            if tool_name not in self._config.allowed_tools:
                return ToolExecutionResult(
                    tool_name=tool_name,
                    success=False,
                    error=f"工具 {tool_name} 不在允许列表中",
                )

        # 验证必需参数
        for required in tool.required_params:
            if required not in params:
                return ToolExecutionResult(
                    tool_name=tool_name,
                    success=False,
                    error=f"缺少必需参数: {required}",
                )

        # 执行工具
        try:
            handler = self._handlers.get(tool_name)
            if handler:
                # 设置超时
                timeout = self._config.tool_timeout if self._config else 30
                try:
                    if asyncio.iscoroutinefunction(handler):
                        result = await asyncio.wait_for(handler(**params), timeout=timeout)
                    else:
                        result = await asyncio.wait_for(
                            asyncio.to_thread(handler, **params),
                            timeout=timeout
                        )
                except asyncio.TimeoutError:
                    return ToolExecutionResult(
                        tool_name=tool_name,
                        success=False,
                        error=f"工具执行超时 ({timeout}s)",
                        execution_time_ms=(time.time() - start_time) * 1000,
                    )
            else:
                # 没有注册 handler，返回模拟结果
                result = {"message": f"工具 {tool_name} 已调用", "params": params}

            execution_time_ms = (time.time() - start_time) * 1000
            self.update_metrics(True, execution_time_ms)

            return ToolExecutionResult(
                tool_name=tool_name,
                success=True,
                result=result,
                execution_time_ms=execution_time_ms,
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            self.update_metrics(False, execution_time_ms)

            return ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                error=str(e),
                execution_time_ms=execution_time_ms,
            )

    async def discover(
        self,
        task_description: str
    ) -> List[ToolDefinition]:
        """根据任务描述发现相关工具"""
        start_time = time.time()

        relevant_tools = []
        description_lower = task_description.lower()

        # 关键词匹配
        keyword_map = {
            "file": ["读取", "写入", "文件", "file", "read", "write"],
            "web": ["搜索", "网络", "网页", "search", "web", "url"],
            "code": ["代码", "执行", "运行", "code", "exec", "run"],
            "system": ["命令", "shell", "bash", "terminal"],
        }

        matched_categories = set()
        for category, keywords in keyword_map.items():
            for keyword in keywords:
                if keyword in description_lower:
                    matched_categories.add(category)
                    break

        # 获取匹配类别的工具
        for tool in self._tools.values():
            if tool.enabled:
                if not matched_categories or tool.category in matched_categories:
                    relevant_tools.append(tool)

        latency_ms = (time.time() - start_time) * 1000
        self.update_metrics(True, latency_ms)

        return relevant_tools
