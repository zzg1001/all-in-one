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

    # Storage Type: "local" or "minio"
    # 可以统一配置，也可以分别配置每种存储类型
    storage_type: str = "local"  # 默认存储类型（被下面的具体配置覆盖）

    # 分类存储配置（留空则使用 storage_type 的值）
    skills_storage_type: str = "minio"       # Skills → MinIO（远程共享）
    file_manage_storage_type: str = "minio"  # File Manage → MinIO（远程共享）
    uploads_storage_type: str = ""           # 输入框上传 → 默认本地
    outputs_storage_type: str = ""           # Outputs → 默认本地

    # Local Storage Paths
    local_storage_base_path: str = ""  # 本地存储根目录
    outputs_dir: str = ""
    uploads_dir: str = ""              # 输入框临时上传
    file_manage_dir: str = ""          # File Manage 文件（独立目录）
    skills_storage_dir: str = ""
    skills_storage_temp_dir: str = ""

    # MinIO Configuration (当 storage_type = "minio" 时使用)
    minio_endpoint: str = "8.153.198.194"
    minio_port: int = 8092
    minio_access_key: str = "admin"
    minio_secret_key: str = "yourpassword123"
    minio_secure: bool = False  # 是否使用 HTTPS
    minio_region: str = ""

    # MinIO Buckets (每个存储类别一个 bucket)
    minio_default_bucket: str = "ai-skills"
    minio_skills_bucket: str = "ai-skills"
    minio_file_manage_bucket: str = "ai-file-manage"  # File Manage 专用
    minio_uploads_bucket: str = "ai-uploads"
    minio_outputs_bucket: str = "ai-outputs"

    # Vector Database（配置了 URL 就启用，不配置就不用）
    vector_db_url: str = ""

    @property
    def vector_db_enabled(self) -> bool:
        """向量数据库是否启用（根据 URL 是否配置自动判断）"""
        return bool(self.vector_db_url)

    # JWT (用于 Admin)
    secret_key: str = "change-this-to-random-string"

    # Cleanup Task
    cleanup_interval_hours: int = 24   # 清理任务执行间隔（小时）

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 设置本地存储基础路径
        if not self.local_storage_base_path:
            self.local_storage_base_path = str(SERVER_DIR)

        # DEBUG=true 开发环境，使用相对路径
        # DEBUG=false 生产环境，使用配置的路径
        is_dev = self.debug

        def resolve_path(configured_path: str, default_name: str) -> str:
            """解析路径：开发环境用相对路径，生产环境用配置路径"""
            if not configured_path:
                return str(SERVER_DIR / default_name)
            # 开发环境：忽略 /app/xxx，使用相对路径
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

    def get_storage_type_for(self, category: str) -> str:
        """获取指定类别的存储类型

        Args:
            category: "skills", "file_manage", "uploads", "outputs"

        Returns:
            "local" 或 "minio"
        """
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
# 统一的路径获取函数，所有模块都应该使用这些函数获取路径

def get_outputs_dir() -> Path:
    """获取输出目录"""
    path = Path(get_settings().outputs_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_uploads_dir() -> Path:
    """获取上传目录（输入框临时上传）"""
    path = Path(get_settings().uploads_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_file_manage_dir() -> Path:
    """获取 File Manage 目录（独立目录，启动时从 MinIO 同步）"""
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


# 启动时创建目录（模块加载时初始化）
OUTPUTS_DIR = get_outputs_dir()
UPLOADS_DIR = get_uploads_dir()
FILE_MANAGE_DIR = get_file_manage_dir()
SKILLS_STORAGE_DIR = get_skills_storage_dir()
SKILLS_STORAGE_TEMP_DIR = get_skills_storage_temp_dir()
