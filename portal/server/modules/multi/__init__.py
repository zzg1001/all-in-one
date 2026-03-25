"""
多Agent模块导出
多 Agent 协同的 4 大组件
"""

from modules.multi.registry import RegistryModule
from modules.multi.orchestrator import OrchestratorModule
from modules.multi.bus import BusModule
from modules.multi.governance import GovernanceModule

__all__ = [
    "RegistryModule",
    "OrchestratorModule",
    "BusModule",
    "GovernanceModule",
]
