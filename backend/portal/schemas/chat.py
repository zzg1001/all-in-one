from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime


class MessageCreate(BaseModel):
    """创建消息"""
    role: str = Field(..., pattern="^(user|agent)$")
    content: str
    metadata: Optional[Dict[str, Any]] = None  # skill_plan, attachments 等
    created_at: Optional[datetime] = None  # 前端指定的时间戳


class MessageResponse(BaseModel):
    """消息响应"""
    id: str
    session_id: str
    role: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_model(cls, msg):
        """从 ORM 模型转换，处理字段映射"""
        return cls(
            id=msg.id,
            session_id=msg.session_id,
            role=msg.role,
            content=msg.content,
            metadata=msg.extra_data,
            created_at=msg.created_at
        )


class SessionCreate(BaseModel):
    """创建会话"""
    title: Optional[str] = None


class SessionUpdate(BaseModel):
    """更新会话"""
    title: Optional[str] = Field(None, max_length=200)


class SessionResponse(BaseModel):
    """会话响应"""
    id: str
    user_id: str
    title: Optional[str] = None
    message_count: int = 0
    skill_names: Optional[List[str]] = None  # 涉及的技能名称
    last_message_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SessionWithMessages(SessionResponse):
    """会话详情（含消息）"""
    messages: List[MessageResponse] = []


class SessionListResponse(BaseModel):
    """会话列表响应"""
    sessions: List[SessionResponse]
    total: int
