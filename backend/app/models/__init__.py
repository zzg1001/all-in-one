"""
Database Models
"""
from app.models.ccconfig import CCConfig
from app.models.user import User, DEPARTMENTS, ROLES

__all__ = ["CCConfig", "User", "DEPARTMENTS", "ROLES"]
