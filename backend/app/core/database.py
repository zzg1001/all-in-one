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
    from app.models import User  # noqa: F401

    Base.metadata.create_all(bind=engine)

    # 运行数据库迁移
    _run_migrations()

    # 初始化默认用户
    from app.core.init_users import init_default_users
    db = SessionLocal()
    try:
        init_default_users(db)
    finally:
        db.close()


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

        conn.commit()
