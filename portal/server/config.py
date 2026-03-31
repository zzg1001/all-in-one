from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from pathlib import Path
from dotenv import load_dotenv

# 服务器根目录
SERVER_DIR = Path(__file__).parent
PROJECT_ROOT = SERVER_DIR.parent.parent  # all-in-one 根目录

# 按优先级加载配置: .env > ../../../deploy.env
load_dotenv(SERVER_DIR / ".env")
load_dotenv(PROJECT_ROOT / "deploy.env")


class Settings(BaseSettings):
    # Database
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "ai_agent"

    # Claude AI
    anthropic_api_key: str = ""
    anthropic_auth_token: str = ""  # Azure 代理用这个
    anthropic_base_url: str = ""
    claude_model: str = "claude-opus-4-5"

    # App
    debug: bool = False

    # Storage Paths (默认使用相对路径，无需配置)
    outputs_dir: str = ""
    uploads_dir: str = ""
    skills_storage_dir: str = ""
    skills_storage_temp_dir: str = ""

    # Vector Database
    vector_db_url: str = ""

    # JWT (用于 Admin)
    secret_key: str = "change-this-to-random-string"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 如果未配置路径，使用默认相对路径
        if not self.outputs_dir:
            self.outputs_dir = str(SERVER_DIR / "outputs")
        if not self.uploads_dir:
            self.uploads_dir = str(SERVER_DIR / "uploads")
        if not self.skills_storage_dir:
            self.skills_storage_dir = str(SERVER_DIR / "skills_storage")
        if not self.skills_storage_temp_dir:
            self.skills_storage_temp_dir = str(SERVER_DIR / "skills_storage_temp")

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
