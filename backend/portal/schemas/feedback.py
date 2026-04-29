"""用户反馈 Pydantic 模式"""
from pydantic import BaseModel
from typing import Optional, Literal, List
from datetime import datetime


class FeedbackCreate(BaseModel):
    """创建反馈"""
    feedback_type: Literal["bug", "suggestion", "other"]
    title: str
    description: Optional[str] = None
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None


class FeedbackResponse(BaseModel):
    """反馈响应"""
    id: str
    user_id: str
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    feedback_type: str
    title: str
    description: Optional[str] = None
    status: str
    admin_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FeedbackUpdate(BaseModel):
    """更新反馈（管理端）"""
    status: Optional[Literal["pending", "processing", "resolved", "closed"]] = None
    admin_notes: Optional[str] = None


class FeedbackListResponse(BaseModel):
    """反馈列表响应"""
    items: List[FeedbackResponse]
    total: int
