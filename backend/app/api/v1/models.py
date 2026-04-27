"""
Models API - 模型配置管理
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from app.core.database import get_db

router = APIRouter()


class ModelConfigCreate(BaseModel):
    name: str
    provider: str  # anthropic, openai, azure
    model_id: str
    api_key: str
    base_url: Optional[str] = None
    max_tokens: Optional[int] = 4096
    temperature: Optional[float] = 0.7


class ModelConfigUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    model_id: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    is_active: Optional[bool] = None


@router.get("")
async def list_models(db: Session = Depends(get_db)):
    """获取所有模型配置"""
    # TODO: 从数据库获取
    return [
        {
            "id": "1",
            "name": "Claude Opus",
            "provider": "anthropic",
            "model_id": "claude-opus-4-5",
            "api_key": "****",
            "base_url": None,
            "max_tokens": 4096,
            "temperature": 0.7,
            "is_active": True,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
    ]


@router.get("/{model_id}")
async def get_model(model_id: str, db: Session = Depends(get_db)):
    """获取单个模型配置"""
    # TODO: 从数据库获取
    raise HTTPException(status_code=404, detail="Model not found")


@router.post("")
async def create_model(data: ModelConfigCreate, db: Session = Depends(get_db)):
    """创建模型配置"""
    # TODO: 保存到数据库
    return {"id": "new-id", **data.model_dump()}


@router.put("/{model_id}")
async def update_model(model_id: str, data: ModelConfigUpdate, db: Session = Depends(get_db)):
    """更新模型配置"""
    # TODO: 更新数据库
    return {"id": model_id, "message": "Updated"}


@router.delete("/{model_id}")
async def delete_model(model_id: str, db: Session = Depends(get_db)):
    """删除模型配置"""
    # TODO: 从数据库删除
    return {"message": "Deleted"}


@router.post("/{model_id}/test")
async def test_model(model_id: str, db: Session = Depends(get_db)):
    """测试模型连接"""
    # TODO: 实际测试 API 连接
    return {"success": True, "message": "Connection successful"}
