"""
Admin API Configuration
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List
import json


class Settings(BaseSettings):
    # Server
    admin_api_url: str = "http://127.0.0.1:8001/api"

    @property
    def server_host(self) -> str:
        from urllib.parse import urlparse
        parsed = urlparse(self.admin_api_url)
        return parsed.hostname or "127.0.0.1"

    @property
    def server_port(self) -> int:
        from urllib.parse import urlparse
        parsed = urlparse(self.admin_api_url)
        return parsed.port or 8001

    # Environment
    env: str = "development"
    debug: bool = True

    # Database (共享 Portal 的数据库)
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "product_background"

    # JWT Auth
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS
    cors_origins_str: str = '["http://localhost:5174"]'

    # Portal API (用于跨服务调用)
    portal_api_url: str = "http://localhost:8000/api"

    @property
    def cors_origins(self) -> List[str]:
        try:
            return json.loads(self.cors_origins_str)
        except json.JSONDecodeError:
            return ["http://localhost:5174"]

    @property
    def database_url(self) -> str:
        return f"mysql+pymysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
