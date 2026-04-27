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

    # 初始化默认用户
    from app.core.init_users import init_default_users
    db = SessionLocal()
    try:
        init_default_users(db)
    finally:
        db.close()
