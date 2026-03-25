from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import get_settings
import os

settings = get_settings()

# 使用 SQLite 作为本地开发数据库（如果 MySQL 不可用）
USE_SQLITE = os.getenv("USE_SQLITE", "false").lower() == "true"

if USE_SQLITE:
    # SQLite 本地数据库
    db_path = os.path.join(os.path.dirname(__file__), "data.db")
    database_url = f"sqlite:///{db_path}"
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        echo=settings.debug
    )
else:
    # MySQL 数据库
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=10,        # 连接池大小（默认5）
        max_overflow=20,     # 允许的额外连接数（默认10）
        pool_timeout=60,     # 获取连接的超时时间（默认30秒）
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
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
