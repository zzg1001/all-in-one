"""
依赖注入 - 认证和权限检查
"""
from typing import List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session, Query

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User


class DataScopeType(str, Enum):
    """数据范围类型"""
    SELF = "self"           # 只能看自己的数据
    DEPARTMENT = "dept"     # 能看本部门的数据
    ALL = "all"             # 能看所有数据


@dataclass
class DataScope:
    """
    数据权限范围

    根据用户角色决定可访问的数据范围：
    - user: 只能看自己创建的数据
    - boss: 能看本部门所有人的数据
    - admin: 能看全部数据
    """
    scope_type: DataScopeType
    user_id: str
    department: Optional[str]
    user_ids: Optional[List[str]] = None  # 部门内所有用户ID

    def apply_filter(self, query: Query, owner_field: Any) -> Query:
        """
        应用数据权限过滤

        Args:
            query: SQLAlchemy 查询对象
            owner_field: 所有者字段（如 Model.created_by 或 Model.user_id）

        Returns:
            过滤后的查询
        """
        if self.scope_type == DataScopeType.ALL:
            return query
        elif self.scope_type == DataScopeType.DEPARTMENT:
            if self.user_ids:
                return query.filter(owner_field.in_(self.user_ids))
            return query.filter(owner_field == self.user_id)
        else:  # SELF
            return query.filter(owner_field == self.user_id)

# HTTP Bearer 认证
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    从 JWT token 获取当前用户

    Returns:
        User 对象，未认证返回 None
    """
    if not credentials:
        return None

    token = credentials.credentials
    payload = decode_token(token)

    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        return None

    return user


async def get_current_user_required(
    user: Optional[User] = Depends(get_current_user)
) -> User:
    """
    要求用户必须登录

    Raises:
        HTTPException: 401 如果未登录
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或登录已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_role(allowed_roles: List[str]):
    """
    角色权限检查装饰器

    Args:
        allowed_roles: 允许的角色列表

    Returns:
        依赖函数
    """
    async def role_checker(
        user: User = Depends(get_current_user_required)
    ) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要以下角色之一: {', '.join(allowed_roles)}"
            )
        return user

    return role_checker


def require_admin():
    """要求管理员权限"""
    return require_role(["admin"])


def require_boss_or_admin():
    """要求老板或管理员权限"""
    return require_role(["boss", "admin"])


async def get_current_admin(
    user: User = Depends(require_role(["admin"]))
) -> User:
    """获取当前管理员用户"""
    return user


async def check_agent_access(
    agent_name: str,
    user: User = Depends(get_current_user_required)
) -> User:
    """
    检查用户是否有权访问指定 Agent

    Args:
        agent_name: Agent 名称

    Raises:
        HTTPException: 403 如果无权访问
    """
    if not user.can_access_agent(agent_name):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"您没有权限访问 {agent_name}"
        )
    return user


async def get_data_scope(
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
) -> DataScope:
    """
    获取当前用户的数据访问范围

    根据角色决定数据范围：
    - admin: 全部数据
    - boss: 本部门数据（如果有部门）或全部数据（如果没有部门，如CEO）
    - user: 仅自己的数据

    Returns:
        DataScope 对象，用于过滤查询
    """
    if user.role == "admin":
        return DataScope(
            scope_type=DataScopeType.ALL,
            user_id=user.id,
            department=user.department
        )

    if user.role == "boss":
        # Boss 没有部门（如 CEO）可以看所有数据
        if not user.department:
            return DataScope(
                scope_type=DataScopeType.ALL,
                user_id=user.id,
                department=None
            )

        # 获取同部门的所有用户ID
        dept_users = db.query(User.id).filter(
            User.department == user.department,
            User.is_active == True
        ).all()
        user_ids = [u.id for u in dept_users]

        return DataScope(
            scope_type=DataScopeType.DEPARTMENT,
            user_id=user.id,
            department=user.department,
            user_ids=user_ids
        )

    # 普通用户只能看自己的数据
    return DataScope(
        scope_type=DataScopeType.SELF,
        user_id=user.id,
        department=user.department
    )


async def get_data_scope_optional(
    user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Optional[DataScope]:
    """
    获取数据访问范围（可选，未登录返回 None）
    """
    if not user:
        return None
    return await get_data_scope(user, db)
