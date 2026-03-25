"""
初始化默认 Claude 配置
运行: python init_config.py
"""
import os
import sys
sys.path.insert(0, '.')

from datetime import datetime
from app.core.database import SessionLocal, engine, Base
from app.models.ccconfig import CCConfig

# 创建表
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    # 检查是否已有配置
    existing = db.query(CCConfig).filter(CCConfig.name == 'Claude Opus 4.5 (Azure)').first()

    if existing:
        print(f"配置已存在: {existing.name} (ID: {existing.id})")
        # 确保激活
        if not existing.is_active:
            db.query(CCConfig).update({"is_active": False})
            existing.is_active = True
            db.commit()
            print("✅ 已激活该配置")
    else:
        # 先禁用所有配置
        db.query(CCConfig).update({"is_active": False})

        # 创建默认配置
        config = CCConfig(
            id="default1",
            name="Claude Opus 4.5 (Azure)",
            description="默认配置 - Azure 代理的 Claude Opus 4.5 模型",
            model_id="claude-opus-4-5",
            api_key=os.getenv("AZURE_API_KEY", ""),
            base_url="https://yunqinghu-3344-resource.services.ai.azure.com/anthropic/",
            max_tokens=4096,
            temperature=0.7,
            top_p=1.0,
            system_prompt=None,
            extra_params=None,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(config)
        db.commit()
        print("✅ 已创建并激活默认配置: Claude Opus 4.5 (Azure)")

    # 显示当前所有配置
    print("\n当前配置列表:")
    configs = db.query(CCConfig).all()
    for c in configs:
        status = "✓ 激活" if c.is_active else "  未激活"
        print(f"  {status} | {c.name} | {c.model_id}")

except Exception as e:
    print(f"❌ 错误: {e}")
    db.rollback()
finally:
    db.close()
