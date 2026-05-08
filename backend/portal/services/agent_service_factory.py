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


def get_agent_service(db: Session):
    """
    获取 Agent 服务

    Returns:
        AgentSDKService 服务实例（支持 skill 调用）
    """
    # 获取激活的配置
    active_config = db.query(CCConfig).filter(CCConfig.is_active == True).first()

    if active_config:
        print(f"[AgentServiceFactory] 使用数据库配置: {active_config.name}")
        print(f"[AgentServiceFactory] 模型: {active_config.model_id}")
        print(f"[AgentServiceFactory] Base URL: {active_config.base_url or '默认'}")
    else:
        print(f"[AgentServiceFactory] 使用环境变量配置")
        print(f"[AgentServiceFactory] 模型: {settings.claude_model}")

    # 使用 AgentSDKService - 支持 skill 调用
    from portal.services.agent_service_sdk import AgentSDKService
    print(f"[AgentServiceFactory] 创建 AgentSDKService（支持 Skill 调用）")
    return AgentSDKService(db)
