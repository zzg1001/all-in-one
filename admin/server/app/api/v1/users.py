"""
Users API - 用户管理
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import hash_password
from app.core.deps import get_current_admin
from app.models.user import User, DEPARTMENTS, ROLES

router = APIRouter()


class UserCreate(BaseModel):
    username: str
    password: str
    display_name: Optional[str] = None
    department: Optional[str] = None
    role: str = "user"
    is_active: bool = True


class UserUpdate(BaseModel):
    username: Optional[str] = None
    display_name: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserResetPassword(BaseModel):
    new_password: str


class UserResponse(BaseModel):
    id: str
    username: str
    display_name: Optional[str]
    department: Optional[str]
    role: str
    is_active: bool
    created_at: Optional[str]
    last_login: Optional[str]

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    total: int
    items: List[dict]


@router.get("/departments")
async def list_departments():
    """获取部门列表"""
    return DEPARTMENTS


@router.get("/roles")
async def list_roles():
    """获取角色列表"""
    return ROLES


@router.get("", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    department: Optional[str] = None,
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    """获取用户列表（需要管理员权限）"""
    query = db.query(User)

    # 搜索过滤
    if search:
        query = query.filter(
            (User.username.contains(search)) |
            (User.display_name.contains(search))
        )

    # 部门过滤
    if department:
        query = query.filter(User.department == department)

    # 角色过滤
    if role:
        query = query.filter(User.role == role)

    # 总数
    total = query.count()

    # 分页
    users = query.order_by(User.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    return UserListResponse(
        total=total,
        items=[u.to_dict() for u in users]
    )


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    """获取单个用户（需要管理员权限）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user.to_dict()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    """创建用户（需要管理员权限）"""
    # 检查用户名是否已存在
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    # 验证部门
    if data.department and data.department not in DEPARTMENTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的部门，可选值: {', '.join(DEPARTMENTS)}"
        )

    # 验证角色
    if data.role not in ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的角色，可选值: {', '.join(ROLES)}"
        )

    # 创建用户
    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        display_name=data.display_name,
        department=data.department,
        role=data.role,
        is_active=data.is_active
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user.to_dict()


@router.put("/{user_id}")
async def update_user(
    user_id: str,
    data: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    """更新用户（需要管理员权限）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 更新用户名
    if data.username is not None and data.username != user.username:
        existing = db.query(User).filter(User.username == data.username).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        user.username = data.username

    # 更新显示名称
    if data.display_name is not None:
        user.display_name = data.display_name

    # 更新部门
    if data.department is not None:
        if data.department and data.department not in DEPARTMENTS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的部门，可选值: {', '.join(DEPARTMENTS)}"
            )
        user.department = data.department

    # 更新角色
    if data.role is not None:
        if data.role not in ROLES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的角色，可选值: {', '.join(ROLES)}"
            )
        user.role = data.role

    # 更新状态
    if data.is_active is not None:
        user.is_active = data.is_active

    db.commit()
    db.refresh(user)

    return user.to_dict()


@router.put("/{user_id}/password")
async def reset_user_password(
    user_id: str,
    data: UserResetPassword,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    """重置用户密码（需要管理员权限）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.password_hash = hash_password(data.new_password)
    db.commit()

    return {"message": "密码重置成功"}


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """删除用户（需要管理员权限）"""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    db.delete(user)
    db.commit()

    return {"message": "用户已删除"}
