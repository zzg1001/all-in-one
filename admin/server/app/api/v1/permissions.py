"""
Permissions API - 权限管理
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from app.core.database import get_db

router = APIRouter()


class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: List[str] = []


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None


# ============ Roles ============

@router.get("/roles")
async def list_roles(db: Session = Depends(get_db)):
    """获取角色列表"""
    return [
        {"id": "admin", "name": "管理员", "permissions": ["*"]},
        {"id": "user", "name": "普通用户", "permissions": ["read", "execute"]},
    ]


@router.post("/roles")
async def create_role(data: RoleCreate, db: Session = Depends(get_db)):
    """创建角色"""
    return {"id": "new-role", **data.model_dump()}


@router.put("/roles/{role_id}")
async def update_role(role_id: str, data: RoleUpdate, db: Session = Depends(get_db)):
    """更新角色"""
    return {"id": role_id, "message": "Updated"}


@router.delete("/roles/{role_id}")
async def delete_role(role_id: str, db: Session = Depends(get_db)):
    """删除角色"""
    return {"message": "Deleted"}


# ============ Permissions ============

@router.get("/available")
async def list_available_permissions():
    """获取所有可用权限"""
    return [
        {"id": "read", "name": "读取", "description": "查看技能和工作流"},
        {"id": "execute", "name": "执行", "description": "执行技能和工作流"},
        {"id": "create", "name": "创建", "description": "创建技能和工作流"},
        {"id": "update", "name": "更新", "description": "更新技能和工作流"},
        {"id": "delete", "name": "删除", "description": "删除技能和工作流"},
        {"id": "admin", "name": "管理", "description": "管理系统配置"},
    ]


# ============ User Permissions ============

@router.get("/user/{user_id}")
async def get_user_permissions(user_id: str, db: Session = Depends(get_db)):
    """获取用户权限"""
    return {"user_id": user_id, "role": "user", "permissions": ["read", "execute"]}


@router.put("/user/{user_id}")
async def update_user_permissions(user_id: str, data: dict, db: Session = Depends(get_db)):
    """更新用户权限"""
    return {"user_id": user_id, "message": "Updated"}
