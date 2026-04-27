"""
模块化架构 - 模块注册表和导出

这是模块系统的入口点，负责：
1. 注册和管理所有模块实例
2. 提供模块发现和查找功能
3. 导出公共接口
"""

from typing import Dict, List, Optional, Type
from .base import (
    # 枚举
    ModuleStatus,
    ModuleType,
    ModuleCategory,
    # 配置
    ModuleConfig,
    MemoryModuleConfig,
    ReasoningModuleConfig,
    PlanningModuleConfig,
    ToolsModuleConfig,
    ActionsModuleConfig,
    RegistryModuleConfig,
    OrchestratorModuleConfig,
    BusModuleConfig,
    GovernanceModuleConfig,
    MODULE_CONFIG_MAP,
    # 指标
    ModuleMetrics,
    # 事件
    ModuleEvent,
    ModuleEventBus,
    event_bus,
    # 基类
    BaseModule,
    IModule,
    # 定义
    ModuleDefinition,
    MODULE_DEFINITIONS,
    get_module_definition,
    get_config_class,
)
import logging

logger = logging.getLogger(__name__)


class ModuleRegistry:
    """模块注册表 - 管理所有模块实例"""

    _instance: Optional["ModuleRegistry"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._modules: Dict[str, Dict[str, BaseModule]] = {}  # agent_id -> {module_type -> module}
        self._global_modules: Dict[str, BaseModule] = {}  # 全局模块实例
        self._module_classes: Dict[ModuleType, Type[BaseModule]] = {}  # 模块类型到类的映射
        self._initialized = True

    def register_module_class(self, module_type: ModuleType, module_class: Type[BaseModule]):
        """注册模块类（用于创建实例）"""
        self._module_classes[module_type] = module_class
        logger.info(f"Registered module class: {module_type.value} -> {module_class.__name__}")

    def create_module(self, module_type: ModuleType, agent_id: Optional[str] = None) -> Optional[BaseModule]:
        """创建模块实例"""
        if module_type not in self._module_classes:
            logger.warning(f"Module class not registered: {module_type.value}")
            return None

        module_class = self._module_classes[module_type]
        module = module_class()

        if agent_id:
            if agent_id not in self._modules:
                self._modules[agent_id] = {}
            self._modules[agent_id][module_type.value] = module
        else:
            self._global_modules[module_type.value] = module

        return module

    def get_module(self, module_type: str, agent_id: Optional[str] = None) -> Optional[BaseModule]:
        """获取模块实例"""
        if agent_id:
            return self._modules.get(agent_id, {}).get(module_type)
        return self._global_modules.get(module_type)

    def get_agent_modules(self, agent_id: str) -> Dict[str, BaseModule]:
        """获取Agent的所有模块"""
        return self._modules.get(agent_id, {})

    def list_modules(self, agent_id: Optional[str] = None) -> List[str]:
        """列出所有模块类型"""
        if agent_id:
            return list(self._modules.get(agent_id, {}).keys())
        return list(self._global_modules.keys())

    def remove_agent_modules(self, agent_id: str):
        """移除Agent的所有模块"""
        if agent_id in self._modules:
            del self._modules[agent_id]

    def get_all_metrics(self, agent_id: Optional[str] = None) -> Dict[str, ModuleMetrics]:
        """获取所有模块的指标"""
        modules = self._modules.get(agent_id, {}) if agent_id else self._global_modules
        return {
            module_type: module.get_metrics()
            for module_type, module in modules.items()
        }


# 全局注册表实例
registry = ModuleRegistry()


# ============ 导出 ============

__all__ = [
    # 枚举
    "ModuleStatus",
    "ModuleType",
    "ModuleCategory",
    # 配置
    "ModuleConfig",
    "MemoryModuleConfig",
    "ReasoningModuleConfig",
    "PlanningModuleConfig",
    "ToolsModuleConfig",
    "ActionsModuleConfig",
    "RegistryModuleConfig",
    "OrchestratorModuleConfig",
    "BusModuleConfig",
    "GovernanceModuleConfig",
    "MODULE_CONFIG_MAP",
    # 指标
    "ModuleMetrics",
    # 事件
    "ModuleEvent",
    "ModuleEventBus",
    "event_bus",
    # 基类
    "BaseModule",
    "IModule",
    # 定义
    "ModuleDefinition",
    "MODULE_DEFINITIONS",
    "get_module_definition",
    "get_config_class",
    # 注册表
    "ModuleRegistry",
    "registry",
]
