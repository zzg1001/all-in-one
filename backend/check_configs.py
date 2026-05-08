"""检查数据库中的配置"""
from app.core.database import SessionLocal
from app.models.ccconfig import CCConfig
from app.models.proxy_config import ProxyConfig

db = SessionLocal()

# 检查模型配置
print("=" * 50)
print("模型配置 (ccconfig):")
print("=" * 50)
configs = db.query(CCConfig).all()
print(f"记录数: {len(configs)}")
for c in configs:
    print(f"  - {c.name}: model={c.model_id}, active={c.is_active}")

# 检查代理配置
print("\n" + "=" * 50)
print("代理配置 (proxy_configs):")
print("=" * 50)
proxies = db.query(ProxyConfig).all()
print(f"记录数: {len(proxies)}")
for p in proxies:
    print(f"  - {p.name}: model={p.target_model}, running={p.is_running}")

db.close()
