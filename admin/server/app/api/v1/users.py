"""
Users API - 用户管理
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from app.core.database import get_db

router = APIRouter()


class UserCreate(BaseModel):
    username: str
    email: Optional[str] = None
    password: str
    role: str = "user"


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("")
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取用户列表"""
    # TODO: 从数据库查询
    return []


@router.get("/{user_id}")
async def get_user(user_id: str, db: Session = Depends(get_db)):
    """获取单个用户"""
    # TODO: 从数据库获取
    raise HTTPException(status_code=404, detail="User not found")


@router.post("")
async def create_user(data: UserCreate, db: Session = Depends(get_db)):
    """创建用户"""
    # TODO: 保存到数据库
    return {"id": "new-id", "username": data.username, "email": data.email, "role": data.role}


@router.put("/{user_id}")
async def update_user(user_id: str, data: UserUpdate, db: Session = Depends(get_db)):
    """更新用户"""
    # TODO: 更新数据库
    return {"id": user_id, "message": "Updated"}


@router.delete("/{user_id}")
async def delete_user(user_id: str, db: Session = Depends(get_db)):
    """删除用户"""
    # TODO: 从数据库删除
    return {"message": "Deleted"}
