"""初始化 proxy_configs 表"""
import os
from app.core.database import engine, Base, SessionLocal
from app.models.proxy_config import ProxyConfig

# 创建表
print("创建 proxy_configs 表...")
Base.metadata.create_all(bind=engine, tables=[ProxyConfig.__table__])

# 检查是否有数据
db = SessionLocal()
count = db.query(ProxyConfig).count()
print(f"当前记录数: {count}")

# 如果没有数据，创建默认配置
if count == 0:
    import uuid

    # 配置1: Azure Anthropic (从 .env 读取)
    azure_config = ProxyConfig(
        id=str(uuid.uuid4()),
        name="Azure Anthropic",
        description="Azure 上的 Anthropic API 代理",
        proxy_type="anthropic_to_openai",
        target_base_url=os.getenv("ANTHROPIC_BASE_URL", "https://yunqinghu-3344-resource.services.ai.azure.com/anthropic/"),
        target_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        target_model=os.getenv("CLAUDE_MODEL", "claude-opus-4-5"),
        proxy_port=4000,
        max_tokens=4096,
        temperature=0.7,
        is_enabled=False,
        is_running=False,
    )
    db.add(azure_config)
    print(f"已创建配置: Azure Anthropic")

    # 配置2: DashScope Qwen
    qwen_config = ProxyConfig(
        id=str(uuid.uuid4()),
        name="DashScope Qwen",
        description="阿里云 DashScope Qwen 模型代理",
        proxy_type="anthropic_to_openai",
        target_base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        target_api_key="sk-your-dashscope-api-key",  # 需要在页面上修改
        target_model="qwen-plus",
        proxy_port=4000,
        max_tokens=4096,
        temperature=0.7,
        is_enabled=False,
        is_running=False,
    )
    db.add(qwen_config)
    print(f"已创建配置: DashScope Qwen")

    db.commit()
    print("\n请在管理后台修改 DashScope 的 API Key")

db.close()
print("完成!")
