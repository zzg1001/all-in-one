"""
Agent Service Factory - Agent 服务工厂

统一使用 AgentSDKService，支持：
- Skill 调用（数据库中的技能）
- 工具调用（Tool Use）
- 两种模型配置（qwen 通过代理，Claude 直连 Azure）
"""

from sqlalchemy.orm import Session

from app.models.ccconfig import CCConfig
from app.core.config import get_settings

settings = get_settings()


def get_agent_service(db: Session, agent_id: str = None):
    """
    获取 Agent 服务

    Args:
        db: 数据库会话
        agent_id: Agent ID，用于获取该 Agent 配置的模型

    Returns:
        AgentSDKService 服务实例（支持 skill 调用）
    """
    # 使用 AgentSDKService - 支持 skill 调用
    from portal.services.agent_service_sdk import AgentSDKService
    print(f"[AgentServiceFactory] 创建 AgentSDKService（agent_id={agent_id}）")
    return AgentSDKService(db, agent_id=agent_id)
