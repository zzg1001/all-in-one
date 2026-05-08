"""
Database Models
"""
from app.models.ccconfig import CCConfig
from app.models.user import User, DEPARTMENTS, ROLES
from app.models.proxy_config import ProxyConfig

__all__ = ["CCConfig", "User", "DEPARTMENTS", "ROLES", "ProxyConfig"]
