from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class DataNoteBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    file_type: str = Field(..., max_length=20)
    file_url: Optional[str] = Field(None, max_length=500)
    file_size: Optional[str] = None
    source_skill: Optional[str] = None


class DataNoteCreate(DataNoteBase):
    """创建数据便签"""
    parent_id: Optional[str] = None


class DataNoteUpdate(BaseModel):
    """更新数据便签"""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    is_favorited: Optional[bool] = None
    parent_id: Optional[str] = None


class FolderCreate(BaseModel):
    """创建文件夹"""
    name: str = Field(..., max_length=100)
    parent_id: Optional[str] = None
    item_ids: List[str] = []  # 要移入文件夹的文件ID


class MoveToFolder(BaseModel):
    """移动到文件夹"""
    target_folder_id: Optional[str] = None  # None 表示移到根目录


class DataNoteResponse(BaseModel):
    """数据便签响应"""
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    file_type: str
    file_url: Optional[str] = None
    file_size: Optional[str] = None
    source_skill: Optional[str] = None
    is_favorited: bool = False
    parent_id: Optional[str] = None
    level: int = 0
    item_count: Optional[int] = None  # 文件夹内项目数
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
