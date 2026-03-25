from pydantic import BaseModel
from typing import List, Literal
from datetime import datetime


class FavoriteCreate(BaseModel):
    """添加收藏"""
    item_type: Literal["skill", "workflow"]
    item_id: str


class FavoriteDelete(BaseModel):
    """取消收藏"""
    item_type: Literal["skill", "workflow"]
    item_id: str


class FavoriteResponse(BaseModel):
    """收藏响应"""
    id: str
    user_id: str
    item_type: str
    item_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class FavoriteListResponse(BaseModel):
    """收藏列表响应"""
    skills: List[str]  # 收藏的技能ID列表
    workflows: List[str]  # 收藏的子流程ID列表
