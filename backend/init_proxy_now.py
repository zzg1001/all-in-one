"""强制初始化代理配置"""
import uuid
from app.core.database import engine, Base, SessionLocal
from app.models.proxy_config import ProxyConfig

# 创建表
print("创建 proxy_configs 表...")
Base.metadata.create_all(bind=engine, tables=[ProxyConfig.__table__])

db = SessionLocal()

# 删除旧配置
db.query(ProxyConfig).delete()
db.commit()
print("已清空旧配置")

# 创建新配置
config = ProxyConfig(
    id=str(uuid.uuid4()),
    name="DashScope Qwen",
    description="阿里云 DashScope Qwen 模型代理",
    proxy_type="anthropic_to_openai",
    target_base_url="https://dashscope.aliyuncs.com/apps/anthropic",
    target_api_key="sk-f56f11bb8f0e48a985a655b36ce2970e",
    target_model="qwen3.6-plus",
    proxy_port=4000,
    max_tokens=4096,
    temperature=0.7,
    is_enabled=False,
    is_running=False,
)
db.add(config)
db.commit()
print(f"已创建配置: {config.name}")
print(f"  - URL: {config.target_base_url}")
print(f"  - Model: {config.target_model}")

db.close()
print("\n完成! 重启后端后刷新页面即可看到配置")
