from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# 服务器根目录
SERVER_DIR = Path(__file__).parent


class Settings(BaseSettings):
    # Server
    portal_api_url: str = "http://127.0.0.1:8000/api"

    @property
    def server_host(self) -> str:
        from urllib.parse import urlparse
        parsed = urlparse(self.portal_api_url)
        return parsed.hostname or "127.0.0.1"

    @property
    def server_port(self) -> int:
        from urllib.parse import urlparse
        parsed = urlparse(self.portal_api_url)
        return parsed.port or 8000

    # Database
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "product_background"

    # Claude AI
    anthropic_api_key: str = ""
    anthropic_base_url: str = ""  # Azure proxy URL
    claude_model: str = "claude-opus-4-5"

    # App
    debug: bool = True

    # Storage Paths (可配置，将来可指向文件系统)
    outputs_dir: str = str(SERVER_DIR / "outputs")
    uploads_dir: str = str(SERVER_DIR / "uploads")
    skills_storage_dir: str = str(SERVER_DIR / "skills_storage")
    skills_storage_temp_dir: str = str(SERVER_DIR / "skills_storage_temp")

    # Vector Database (PostgreSQL + pgvector)
    vector_db_url: str = "postgresql://pguser:Password.123@8.153.198.194:8092/pgdb"

    @property
    def database_url(self) -> str:
        return f"mysql+pymysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


# ============ 路径管理 ============
# 统一的路径获取函数，所有模块都应该使用这些函数获取路径

def get_outputs_dir() -> Path:
    """获取输出目录"""
    path = Path(get_settings().outputs_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_uploads_dir() -> Path:
    """获取上传目录"""
    path = Path(get_settings().uploads_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_skills_storage_dir() -> Path:
    """获取技能存储目录"""
    path = Path(get_settings().skills_storage_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_skills_storage_temp_dir() -> Path:
    """获取技能临时存储目录"""
    path = Path(get_settings().skills_storage_temp_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_server_dir() -> Path:
    """获取服务器根目录"""
    return SERVER_DIR


# 兼容性：导出 Path 对象（延迟初始化）
# 注意：这些变量在模块加载时会被初始化，如果配置在运行时改变需要重启
OUTPUTS_DIR = get_outputs_dir()
UPLOADS_DIR = get_uploads_dir()
SKILLS_STORAGE_DIR = get_skills_storage_dir()
SKILLS_STORAGE_TEMP_DIR = get_skills_storage_temp_dir()
