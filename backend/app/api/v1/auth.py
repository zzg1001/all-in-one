"""
Auth API - 认证接口
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, hash_password
from app.core.deps import get_current_user_required
from app.models.user import User

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class PasswordChangeRequest(BaseModel):
    old_password: str
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


@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest, db: Session = Depends(get_db)):
    """
    用户登录

    Args:
        data: 用户名和密码

    Returns:
        JWT token 和用户信息
    """
    # 查找用户
    user = db.query(User).filter(User.username == data.username).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    # 验证密码
    if not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    # 检查账户是否启用
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被禁用"
        )

    # 更新最后登录时间
    user.last_login = datetime.now()
    db.commit()

    # 生成 token
    access_token = create_access_token(data={"sub": user.id})

    return LoginResponse(
        access_token=access_token,
        user=user.to_dict()
    )


@router.post("/logout")
async def logout():
    """
    用户登出

    Note:
        JWT 是无状态的，登出只需客户端删除 token
        这个接口主要用于前端调用的一致性
    """
    return {"message": "登出成功"}


@router.get("/me")
async def get_current_user_info(
    user: User = Depends(get_current_user_required)
):
    """
    获取当前用户信息

    Returns:
        当前登录用户的信息
    """
    return user.to_dict()


@router.put("/password")
async def change_password(
    data: PasswordChangeRequest,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """
    修改密码

    Args:
        data: 旧密码和新密码
    """
    # 验证旧密码
    if not verify_password(data.old_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误"
        )

    # 更新密码
    user.password_hash = hash_password(data.new_password)
    db.commit()

    return {"message": "密码修改成功"}
