"""
Database connection - 统一数据库配置
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import get_settings
import os

settings = get_settings()

# 使用 SQLite 作为本地开发数据库（如果配置）
USE_SQLITE = os.getenv("USE_SQLITE", "false").lower() == "true"

if USE_SQLITE:
    from pathlib import Path
    db_path = Path(__file__).parent.parent.parent / "data.db"
    database_url = f"sqlite:///{db_path}"
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        echo=settings.debug
    )
else:
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=10,
        max_overflow=20,
        pool_timeout=60,
        echo=settings.debug
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables and default data"""
    # 导入所有模型以确保表被创建
    from app.models import User, ProxyConfig  # noqa: F401

    Base.metadata.create_all(bind=engine)

    # 运行数据库迁移
    _run_migrations()

    # 初始化默认用户
    from app.core.init_users import init_default_users
    db = SessionLocal()
    try:
        init_default_users(db)
        # 初始化默认代理配置
        _init_default_proxy_configs(db)
    finally:
        db.close()


def _init_default_proxy_configs(db):
    """初始化默认代理配置"""
    import uuid
    from app.models import ProxyConfig

    # 检查是否已有 DashScope Qwen 配置
    existing = db.query(ProxyConfig).filter(ProxyConfig.name == "DashScope Qwen").first()
    if existing:
        # 更新现有配置
        existing.target_base_url = "https://dashscope.aliyuncs.com/apps/anthropic"
        existing.target_api_key = "sk-f56f11bb8f0e48a985a655b36ce2970e"
        existing.target_model = "qwen3.6-plus"
        # 设置默认的 proxy_url 和 proxy_model（如果未设置）
        if not existing.proxy_url:
            existing.proxy_url = "http://localhost:8001/proxy/v1/messages"
        if not existing.proxy_model:
            existing.proxy_model = "claude-sonnet-4-20250514"
        db.commit()
        print("[Init] 已更新代理配置: DashScope Qwen")
        return

    # 创建 DashScope Qwen 配置
    config = ProxyConfig(
        id=str(uuid.uuid4()),
        name="DashScope Qwen",
        description="阿里云 DashScope Qwen 模型代理",
        proxy_type="anthropic_to_openai",
        target_base_url="https://dashscope.aliyuncs.com/apps/anthropic",
        target_api_key="sk-f56f11bb8f0e48a985a655b36ce2970e",
        target_model="qwen3.6-plus",
        proxy_url="http://localhost:8001/proxy/v1/messages",
        proxy_model="claude-sonnet-4-20250514",
        proxy_port=4000,
        max_tokens=4096,
        temperature=0.7,
        is_enabled=False,
        is_running=False,
    )
    db.add(config)
    db.commit()
    print("[Init] 已创建默认代理配置: DashScope Qwen")


def _run_migrations():
    """运行数据库迁移 - 添加缺失的列"""
    from sqlalchemy import text, inspect

    inspector = inspect(engine)

    with engine.connect() as conn:
        # user_feedbacks 表迁移
        if 'user_feedbacks' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('user_feedbacks')]

            if 'agent_id' not in columns:
                conn.execute(text('ALTER TABLE user_feedbacks ADD COLUMN agent_id VARCHAR(50)'))
                print('[Migration] Added agent_id column to user_feedbacks')

            if 'agent_name' not in columns:
                conn.execute(text('ALTER TABLE user_feedbacks ADD COLUMN agent_name VARCHAR(100)'))
                print('[Migration] Added agent_name column to user_feedbacks')

            if 'updated_at' not in columns:
                conn.execute(text('ALTER TABLE user_feedbacks ADD COLUMN updated_at DATETIME'))
                print('[Migration] Added updated_at column to user_feedbacks')

        # agents 表迁移
        if 'agents' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('agents')]

            if 'accessible_agent_ids' not in columns:
                conn.execute(text('ALTER TABLE agents ADD COLUMN accessible_agent_ids JSON'))
                print('[Migration] Added accessible_agent_ids column to agents')

        # proxy_configs 表迁移
        if 'proxy_configs' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('proxy_configs')]

            # 添加 proxy_url 列（代理地址）
            if 'proxy_url' not in columns:
                conn.execute(text('ALTER TABLE proxy_configs ADD COLUMN proxy_url VARCHAR(500)'))
                print('[Migration] Added proxy_url column to proxy_configs')

            # 添加 proxy_model 列（对外模型名）
            if 'proxy_model' not in columns:
                conn.execute(text('ALTER TABLE proxy_configs ADD COLUMN proxy_model VARCHAR(100)'))
                print('[Migration] Added proxy_model column to proxy_configs')

            # 如果有旧的 display_base_url 列，迁移数据并删除
            if 'display_base_url' in columns:
                conn.execute(text('UPDATE proxy_configs SET proxy_url = display_base_url WHERE proxy_url IS NULL'))
                conn.execute(text('ALTER TABLE proxy_configs DROP COLUMN display_base_url'))
                print('[Migration] Migrated display_base_url to proxy_url')

            # 添加 pid 列（进程 PID）
            if 'pid' not in columns:
                conn.execute(text('ALTER TABLE proxy_configs ADD COLUMN pid INT'))
                print('[Migration] Added pid column to proxy_configs')

        conn.commit()
