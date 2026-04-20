"""
模块化架构基础设施
提供所有模块的基类、接口定义和事件总线
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Protocol, TypeVar, Generic
from pydantic import BaseModel, Field
from datetime import datetime
import asyncio
import logging
import uuid

logger = logging.getLogger(__name__)


# ============ 枚举定义 ============

class ModuleStatus(str, Enum):
    """模块状态枚举"""
    INACTIVE = "inactive"       # 未激活
    INITIALIZING = "initializing"  # 初始化中
    ACTIVE = "active"           # 运行中
    ERROR = "error"             # 错误
    PAUSED = "paused"           # 暂停


class ModuleType(str, Enum):
    """模块类型枚举"""
    # 核心模块
    MEMORY = "memory"
    REASONING = "reasoning"
    PLANNING = "planning"
    TOOLS = "tools"
    ACTIONS = "actions"
    # 多Agent模块
    REGISTRY = "registry"
    ORCHESTRATOR = "orchestrator"
    BUS = "bus"
    GOVERNANCE = "governance"


class ModuleCategory(str, Enum):
    """模块分类"""
    CORE = "core"       # 单Agent核心组件
    MULTI = "multi"     # 多Agent协同组件


# ============ 配置模型 ============

class ModuleConfig(BaseModel):
    """模块配置基类"""
    enabled: bool = True
    priority: int = Field(default=0, description="优先级，数字越小优先级越高")
    settings: Dict[str, Any] = Field(default_factory=dict, description="模块特定设置")

    class Config:
        extra = "allow"


class MemoryModuleConfig(ModuleConfig):
    """Memory模块配置"""
    memory_type: str = Field(default="conversation", description="记忆类型: conversation, vector, hybrid")
    max_history: int = Field(default=20, description="最大历史记录数")
    vector_enabled: bool = Field(default=False, description="是否启用向量存储")
    vector_model: str = Field(default="text-embedding-3-small", description="向量模型")


class ReasoningModuleConfig(ModuleConfig):
    """Reasoning模块配置"""
    reasoning_style: str = Field(default="step-by-step", description="推理风格")
    chain_of_thought: bool = Field(default=True, description="是否使用思维链")
    max_steps: int = Field(default=10, description="最大推理步骤")


class PlanningModuleConfig(ModuleConfig):
    """Planning模块配置"""
    planning_strategy: str = Field(default="hierarchical", description="规划策略")
    max_depth: int = Field(default=5, description="最大规划深度")
    enable_replanning: bool = Field(default=True, description="是否允许重新规划")


class ToolsModuleConfig(ModuleConfig):
    """Tools模块配置"""
    allowed_tools: List[str] = Field(default_factory=list, description="允许的工具列表")
    tool_timeout: int = Field(default=30, description="工具超时时间(秒)")
    parallel_execution: bool = Field(default=False, description="是否允许并行执行")


class ActionsModuleConfig(ModuleConfig):
    """Actions模块配置"""
    max_queue_size: int = Field(default=100, description="最大队列大小")
    retry_count: int = Field(default=3, description="重试次数")
    action_timeout: int = Field(default=60, description="动作超时时间(秒)")


# 多Agent模块配置
class RegistryModuleConfig(ModuleConfig):
    """Registry模块配置"""
    heartbeat_interval: int = Field(default=30, description="心跳间隔(秒)")
    service_ttl: int = Field(default=90, description="服务存活时间(秒)")


class OrchestratorModuleConfig(ModuleConfig):
    """Orchestrator模块配置"""
    execution_mode: str = Field(default="sequential", description="执行模式: sequential, parallel, dag")
    max_concurrent: int = Field(default=5, description="最大并发数")


class BusModuleConfig(ModuleConfig):
    """Agent Bus模块配置"""
    message_ttl: int = Field(default=3600, description="消息存活时间(秒)")
    max_retries: int = Field(default=3, description="最大重试次数")
    routing_strategy: str = Field(default="direct", description="路由策略")


class GovernanceModuleConfig(ModuleConfig):
    """Governance模块配置"""
    enable_audit: bool = Field(default=True, description="是否启用审计")
    rate_limit: int = Field(default=100, description="速率限制(请求/分钟)")
    require_approval: List[str] = Field(default_factory=list, description="需要审批的操作")


# 配置类型映射
MODULE_CONFIG_MAP: Dict[ModuleType, type] = {
    ModuleType.MEMORY: MemoryModuleConfig,
    ModuleType.REASONING: ReasoningModuleConfig,
    ModuleType.PLANNING: PlanningModuleConfig,
    ModuleType.TOOLS: ToolsModuleConfig,
    ModuleType.ACTIONS: ActionsModuleConfig,
    ModuleType.REGISTRY: RegistryModuleConfig,
    ModuleType.ORCHESTRATOR: OrchestratorModuleConfig,
    ModuleType.BUS: BusModuleConfig,
    ModuleType.GOVERNANCE: GovernanceModuleConfig,
}


# ============ 指标模型 ============

class ModuleMetrics(BaseModel):
    """模块运行指标"""
    module_type: str
    status: ModuleStatus = ModuleStatus.INACTIVE
    # 计数
    total_calls: int = 0
    success_count: int = 0
    error_count: int = 0
    # 性能
    avg_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    # 时间戳
    last_activity: Optional[datetime] = None
    started_at: Optional[datetime] = None
    # 额外指标
    extra: Dict[str, Any] = Field(default_factory=dict)


# ============ 事件系统 ============

class ModuleEvent(BaseModel):
    """模块事件"""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    source_module: str
    target_module: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class ModuleEventBus:
    """模块事件总线 - 单例"""
    _instance: Optional["ModuleEventBus"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._handlers: Dict[str, List[Callable]] = {}
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._initialized = True

    def subscribe(self, event_type: str, handler: Callable[[ModuleEvent], Any]):
        """订阅事件"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.debug(f"Handler subscribed to event: {event_type}")

    def unsubscribe(self, event_type: str, handler: Callable):
        """取消订阅"""
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)

    async def publish(self, event: ModuleEvent):
        """发布事件"""
        await self._event_queue.put(event)
        # 同步触发处理（不等待）
        asyncio.create_task(self._process_event(event))

    def publish_sync(self, event: ModuleEvent):
        """同步发布事件（用于非异步上下文）"""
        handlers = self._handlers.get(event.event_type, [])
        handlers.extend(self._handlers.get("*", []))  # 通配符处理器
        for handler in handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    asyncio.create_task(result)
            except Exception as e:
                logger.error(f"Event handler error: {e}")

    async def _process_event(self, event: ModuleEvent):
        """处理单个事件"""
        handlers = self._handlers.get(event.event_type, [])
        handlers.extend(self._handlers.get("*", []))  # 通配符处理器

        for handler in handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Event handler error for {event.event_type}: {e}")

    async def start(self):
        """启动事件循环"""
        self._running = True
        while self._running:
            try:
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                await self._process_event(event)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Event bus error: {e}")

    def stop(self):
        """停止事件循环"""
        self._running = False


# 全局事件总线实例
event_bus = ModuleEventBus()


# ============ 模块接口定义 ============

T = TypeVar('T', bound=ModuleConfig)


class IModule(Protocol[T]):
    """模块接口协议"""

    @property
    def module_type(self) -> ModuleType: ...

    @property
    def module_category(self) -> ModuleCategory: ...

    @property
    def status(self) -> ModuleStatus: ...

    @property
    def config(self) -> T: ...

    async def initialize(self, config: T) -> None: ...

    async def start(self) -> None: ...

    async def stop(self) -> None: ...

    def get_metrics(self) -> ModuleMetrics: ...


# ============ 模块基类 ============

class BaseModule(ABC, Generic[T]):
    """模块抽象基类"""

    def __init__(self, module_type: ModuleType, module_category: ModuleCategory):
        self._module_type = module_type
        self._module_category = module_category
        self._status = ModuleStatus.INACTIVE
        self._config: Optional[T] = None
        self._metrics = ModuleMetrics(module_type=module_type.value)
        self._event_bus = event_bus
        self._logger = logging.getLogger(f"module.{module_type.value}")

    @property
    def module_type(self) -> ModuleType:
        return self._module_type

    @property
    def module_category(self) -> ModuleCategory:
        return self._module_category

    @property
    def status(self) -> ModuleStatus:
        return self._status

    @property
    def config(self) -> Optional[T]:
        return self._config

    async def initialize(self, config: T) -> None:
        """初始化模块"""
        self._status = ModuleStatus.INITIALIZING
        self._config = config

        try:
            await self._on_initialize()
            self._status = ModuleStatus.ACTIVE if config.enabled else ModuleStatus.INACTIVE
            self._metrics.started_at = datetime.now()
            self._logger.info(f"Module {self._module_type.value} initialized")

            # 发布初始化事件
            await self._event_bus.publish(ModuleEvent(
                event_type="module.initialized",
                source_module=self._module_type.value,
                payload={"config": config.model_dump()}
            ))
        except Exception as e:
            self._status = ModuleStatus.ERROR
            self._logger.error(f"Module initialization failed: {e}")
            raise

    async def start(self) -> None:
        """启动模块"""
        if self._status != ModuleStatus.ACTIVE:
            if self._config and self._config.enabled:
                await self._on_start()
                self._status = ModuleStatus.ACTIVE
                self._logger.info(f"Module {self._module_type.value} started")

    async def stop(self) -> None:
        """停止模块"""
        if self._status == ModuleStatus.ACTIVE:
            await self._on_stop()
            self._status = ModuleStatus.INACTIVE
            self._logger.info(f"Module {self._module_type.value} stopped")

    def get_metrics(self) -> ModuleMetrics:
        """获取模块指标"""
        self._metrics.status = self._status
        return self._metrics

    def update_metrics(self, success: bool, latency_ms: float):
        """更新指标"""
        self._metrics.total_calls += 1
        if success:
            self._metrics.success_count += 1
        else:
            self._metrics.error_count += 1

        # 更新延迟指标
        if self._metrics.avg_latency_ms == 0:
            self._metrics.avg_latency_ms = latency_ms
        else:
            self._metrics.avg_latency_ms = (self._metrics.avg_latency_ms * 0.9 + latency_ms * 0.1)
        self._metrics.max_latency_ms = max(self._metrics.max_latency_ms, latency_ms)
        self._metrics.last_activity = datetime.now()

    @abstractmethod
    async def _on_initialize(self) -> None:
        """子类实现初始化逻辑"""
        pass

    async def _on_start(self) -> None:
        """子类可选实现启动逻辑"""
        pass

    async def _on_stop(self) -> None:
        """子类可选实现停止逻辑"""
        pass


# ============ 模块定义（用于API返回） ============

class ModuleDefinition(BaseModel):
    """模块定义，用于前端展示"""
    type: str
    name: str
    description: str
    category: str
    icon: str
    color: str
    config_schema: Dict[str, Any] = Field(default_factory=dict)
    default_config: Dict[str, Any] = Field(default_factory=dict)


# 模块定义列表
MODULE_DEFINITIONS: List[ModuleDefinition] = [
    # 核心模块
    ModuleDefinition(
        type="memory",
        name="Memory",
        description="管理对话历史和上下文记忆，支持短期和长期记忆存储",
        category="core",
        icon="brain",
        color="#8B5CF6",
        default_config=MemoryModuleConfig().model_dump()
    ),
    ModuleDefinition(
        type="reasoning",
        name="Reasoning",
        description="执行逻辑推理和思维链分析，生成结构化的推理过程",
        category="core",
        icon="lightbulb",
        color="#F59E0B",
        default_config=ReasoningModuleConfig().model_dump()
    ),
    ModuleDefinition(
        type="planning",
        name="Planning",
        description="任务分解和执行规划，将复杂任务拆分为可执行步骤",
        category="core",
        icon="map",
        color="#10B981",
        default_config=PlanningModuleConfig().model_dump()
    ),
    ModuleDefinition(
        type="tools",
        name="Tool Use",
        description="工具发现、选择和执行，与外部系统和API交互",
        category="core",
        icon="wrench",
        color="#3B82F6",
        default_config=ToolsModuleConfig().model_dump()
    ),
    ModuleDefinition(
        type="actions",
        name="Actions",
        description="动作执行队列管理，处理异步任务和执行反馈",
        category="core",
        icon="play",
        color="#EF4444",
        default_config=ActionsModuleConfig().model_dump()
    ),
    # 多Agent模块
    ModuleDefinition(
        type="registry",
        name="Registry",
        description="Agent服务注册中心，管理Agent的注册、发现和健康检查",
        category="multi",
        icon="server",
        color="#6366F1",
        default_config=RegistryModuleConfig().model_dump()
    ),
    ModuleDefinition(
        type="orchestrator",
        name="Orchestrator",
        description="多Agent编排器，协调Agent之间的工作流和任务分配",
        category="multi",
        icon="git-branch",
        color="#EC4899",
        default_config=OrchestratorModuleConfig().model_dump()
    ),
    ModuleDefinition(
        type="bus",
        name="Agent Bus",
        description="Agent通信总线，处理Agent间的消息路由和通信",
        category="multi",
        icon="radio",
        color="#14B8A6",
        default_config=BusModuleConfig().model_dump()
    ),
    ModuleDefinition(
        type="governance",
        name="Governance",
        description="治理和权限管理，控制Agent的访问权限和操作审计",
        category="multi",
        icon="shield",
        color="#F97316",
        default_config=GovernanceModuleConfig().model_dump()
    ),
]


def get_module_definition(module_type: str) -> Optional[ModuleDefinition]:
    """根据类型获取模块定义"""
    for defn in MODULE_DEFINITIONS:
        if defn.type == module_type:
            return defn
    return None


def get_config_class(module_type: str) -> type:
    """根据模块类型获取配置类"""
    try:
        mt = ModuleType(module_type)
        return MODULE_CONFIG_MAP.get(mt, ModuleConfig)
    except ValueError:
        return ModuleConfig
