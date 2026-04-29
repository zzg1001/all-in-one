"""用户反馈路由 - Portal API (用户提交)"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from portal.models.feedback import UserFeedback
from portal.schemas.feedback import FeedbackCreate, FeedbackResponse

router = APIRouter(prefix="/api/feedback", tags=["Feedback"])


def get_user_id(x_user_id: Optional[str] = Header(None)) -> str:
    """获取用户ID

    当前：从请求头 X-User-ID 获取，由前端生成的匿名ID
    将来：从 JWT token 或 session 中获取真实用户ID
    """
    if x_user_id:
        return x_user_id
    return "anonymous"


@router.post("", response_model=FeedbackResponse)
async def create_feedback(
    data: FeedbackCreate,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """提交问题反馈"""
    feedback = UserFeedback(
        id=str(uuid.uuid4()),
        user_id=user_id,
        session_id=data.session_id,
        agent_id=data.agent_id,
        agent_name=data.agent_name,
        feedback_type=data.feedback_type,
        title=data.title,
        description=data.description,
        status="pending"
    )

    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return feedback


@router.get("/my", response_model=list[FeedbackResponse])
async def get_my_feedbacks(
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """获取当前用户的反馈列表"""
    feedbacks = db.query(UserFeedback).filter(
        UserFeedback.user_id == user_id
    ).order_by(UserFeedback.created_at.desc()).all()

    return feedbacks
