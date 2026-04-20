"""
多Agent模块导出
多 Agent 协同的 4 大组件
"""

from portal.modules.multi.registry import RegistryModule
from portal.modules.multi.orchestrator import OrchestratorModule
from portal.modules.multi.bus import BusModule
from portal.modules.multi.governance import GovernanceModule

__all__ = [
    "RegistryModule",
    "OrchestratorModule",
    "BusModule",
    "GovernanceModule",
]
