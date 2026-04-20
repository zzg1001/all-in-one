"""
User Model - 用户模型
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text
from datetime import datetime
import uuid

from app.core.database import Base


class User(Base):
    """用户模型"""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    password_hash = Column(String(128), nullable=False, comment="密码哈希")
    display_name = Column(String(100), nullable=True, comment="显示名称")
    department = Column(String(50), nullable=True, comment="部门")
    role = Column(String(20), nullable=False, default="user", comment="角色: user/boss/admin")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    last_login = Column(DateTime, nullable=True, comment="最后登录时间")

    def to_dict(self, include_sensitive=False):
        """转换为字典"""
        data = {
            "id": self.id,
            "username": self.username,
            "display_name": self.display_name or self.username,
            "department": self.department,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
        return data

    def can_access_agent(self, agent_name: str) -> bool:
        """检查用户是否可以访问指定的 Agent"""
        # admin 和 boss 可以访问所有 Agent
        if self.role in ("admin", "boss"):
            return True

        # 普通用户只能访问对应部门的 Agent
        if self.department:
            # Agent 名称格式："{部门}部门 Agent"
            expected_agent = f"{self.department}部门 Agent"
            return agent_name == expected_agent

        return False

    def can_access_admin(self) -> bool:
        """检查用户是否可以访问管理后台"""
        return self.role == "admin"


# 部门列表
DEPARTMENTS = [
    "HR",
    "销售",
    "采购",
    "行政",
    "财务",
]

# 角色列表
ROLES = ["user", "boss", "admin"]
