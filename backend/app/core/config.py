"""
AI Skills Platform API Configuration
统一配置 - 合并 Admin + Portal
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List
from pathlib import Path
from dotenv import load_dotenv
import json
import os

# 目录
SERVER_DIR = Path(__file__).parent.parent.parent  # backend
PROJECT_ROOT = SERVER_DIR.parent  # all-in-one 根目录

# 按优先级加载配置: .env > deploy.env
load_dotenv(SERVER_DIR / ".env")
load_dotenv(PROJECT_ROOT / "deploy.env")


class Settings(BaseSettings):
    # ========== Database ==========
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "ai_agent"

    # ========== Server ==========
    server_host: str = "0.0.0.0"
    server_port: int = 8001
    debug: bool = False

    # ========== JWT Auth ==========
    secret_key: str = "change-this-to-random-string"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # ========== CORS ==========
    cors_origins_str: str = '["*"]'

    @property
    def cors_origins(self) -> List[str]:
        try:
            return json.loads(self.cors_origins_str)
        except json.JSONDecodeError:
            return ["*"]

    # ========== Claude AI (Azure 代理) ==========
    anthropic_auth_token: str = ""
    anthropic_base_url: str = ""
    claude_model: str = "claude-opus-4-5"

    # ========== Storage Type ==========
    storage_type: str = "local"
    skills_storage_type: str = "minio"
    file_manage_storage_type: str = "local"
    uploads_storage_type: str = "local"
    outputs_storage_type: str = "local"

    # ========== Local Storage Paths ==========
    local_storage_base_path: str = ""
    outputs_dir: str = ""
    uploads_dir: str = ""
    file_manage_dir: str = ""
    skills_storage_dir: str = ""
    skills_storage_temp_dir: str = ""

    # ========== MinIO Configuration ==========
    minio_endpoint: str = "8.153.198.194"
    minio_port: int = 8092
    minio_access_key: str = "admin"
    minio_secret_key: str = "yourpassword123"
    minio_secure: bool = False
    minio_region: str = ""

    # MinIO Buckets
    minio_default_bucket: str = "ai-skills"
    minio_skills_bucket: str = "ai-skills"
    minio_skills_temp_bucket: str = "ai-skills-temp"
    minio_file_manage_bucket: str = "ai-file-manage"
    minio_uploads_bucket: str = "ai-uploads"
    minio_outputs_bucket: str = "ai-outputs"

    # ========== Vector Database ==========
    vector_db_url: str = ""

    @property
    def vector_db_enabled(self) -> bool:
        return bool(self.vector_db_url)

    # ========== Cleanup Task ==========
    cleanup_interval_hours: int = 24

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 设置本地存储基础路径
        if not self.local_storage_base_path:
            self.local_storage_base_path = str(SERVER_DIR)

        is_dev = self.debug

        def resolve_path(configured_path: str, default_name: str) -> str:
            if not configured_path:
                return str(SERVER_DIR / default_name)
            if is_dev and configured_path.startswith("/app/"):
                return str(SERVER_DIR / default_name)
            return configured_path

        self.outputs_dir = resolve_path(self.outputs_dir, "outputs")
        self.uploads_dir = resolve_path(self.uploads_dir, "uploads")
        self.file_manage_dir = resolve_path(self.file_manage_dir, "file_manage")
        self.skills_storage_dir = resolve_path(self.skills_storage_dir, "skills_storage")
        self.skills_storage_temp_dir = resolve_path(self.skills_storage_temp_dir, "skills_storage_temp")

    @property
    def database_url(self) -> str:
        return f"mysql+pymysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    def get_anthropic_client_kwargs(self) -> dict:
        """获取 Anthropic client 初始化参数（支持 Azure 代理）"""
        if self.anthropic_base_url and 'azure' in self.anthropic_base_url.lower():
            return {
                "base_url": self.anthropic_base_url,
                "api_key": "placeholder",
                "default_headers": {"Authorization": f"Bearer {self.anthropic_auth_token}"}
            }
        else:
            kwargs = {"api_key": self.anthropic_auth_token}
            if self.anthropic_base_url:
                kwargs["base_url"] = self.anthropic_base_url
            return kwargs

    def get_storage_type_for(self, category: str) -> str:
        """获取指定类别的存储类型"""
        if category == "skills":
            return self.skills_storage_type or self.storage_type
        elif category == "file_manage":
            return self.file_manage_storage_type or self.storage_type
        elif category == "uploads":
            return self.uploads_storage_type or self.storage_type
        elif category == "outputs":
            return self.outputs_storage_type or self.storage_type
        return self.storage_type

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


# ============ 路径管理 ============

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

def get_file_manage_dir() -> Path:
    """获取 File Manage 目录"""
    path = Path(get_settings().file_manage_dir)
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


# 启动时创建目录
OUTPUTS_DIR = get_outputs_dir()
UPLOADS_DIR = get_uploads_dir()
FILE_MANAGE_DIR = get_file_manage_dir()
SKILLS_STORAGE_DIR = get_skills_storage_dir()
SKILLS_STORAGE_TEMP_DIR = get_skills_storage_temp_dir()
