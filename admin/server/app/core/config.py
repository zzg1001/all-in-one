"""
Admin API Configuration
共享 deploy.env 统一配置
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List
from pathlib import Path
from dotenv import load_dotenv
import json

# 目录
SERVER_DIR = Path(__file__).parent.parent.parent  # admin/server
PROJECT_ROOT = SERVER_DIR.parent.parent  # all-in-one 根目录

# 按优先级加载配置: .env > deploy.env
load_dotenv(SERVER_DIR / ".env")
load_dotenv(PROJECT_ROOT / "deploy.env")


class Settings(BaseSettings):
    # Database (与 Portal 共享)
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "ai_agent"

    # Environment
    debug: bool = False

    # JWT Auth
    secret_key: str = "change-this-to-random-string"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS (生产环境自动允许所有)
    cors_origins_str: str = '["*"]'

    @property
    def cors_origins(self) -> List[str]:
        try:
            return json.loads(self.cors_origins_str)
        except json.JSONDecodeError:
            return ["*"]

    @property
    def database_url(self) -> str:
        return f"mysql+pymysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
