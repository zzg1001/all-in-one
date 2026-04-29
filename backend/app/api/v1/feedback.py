"""用户反馈路由 - Admin API (管理查看)"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from app.core.database import get_db
from portal.models.feedback import UserFeedback
from portal.schemas.feedback import FeedbackResponse, FeedbackUpdate, FeedbackListResponse

router = APIRouter(prefix="/api/feedback", tags=["Admin - Feedback"])


@router.get("", response_model=FeedbackListResponse)
async def list_feedbacks(
    status: Optional[str] = Query(None, description="筛选状态"),
    feedback_type: Optional[str] = Query(None, description="筛选类型"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取反馈列表（管理端）"""
    query = db.query(UserFeedback)

    if status:
        query = query.filter(UserFeedback.status == status)
    if feedback_type:
        query = query.filter(UserFeedback.feedback_type == feedback_type)
    if keyword:
        keyword_pattern = f"%{keyword}%"
        query = query.filter(
            (UserFeedback.title.like(keyword_pattern)) |
            (UserFeedback.description.like(keyword_pattern))
        )

    total = query.count()
    items = query.order_by(desc(UserFeedback.created_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return FeedbackListResponse(items=items, total=total)


@router.get("/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback(
    feedback_id: str,
    db: Session = Depends(get_db)
):
    """获取反馈详情"""
    feedback = db.query(UserFeedback).filter(UserFeedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")
    return feedback


@router.put("/{feedback_id}", response_model=FeedbackResponse)
async def update_feedback(
    feedback_id: str,
    data: FeedbackUpdate,
    db: Session = Depends(get_db)
):
    """更新反馈状态/备注（管理端）"""
    feedback = db.query(UserFeedback).filter(UserFeedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")

    if data.status is not None:
        feedback.status = data.status
    if data.admin_notes is not None:
        feedback.admin_notes = data.admin_notes

    # 手动设置更新时间
    feedback.updated_at = datetime.now()

    db.commit()
    db.refresh(feedback)
    return feedback


@router.delete("/{feedback_id}")
async def delete_feedback(
    feedback_id: str,
    db: Session = Depends(get_db)
):
    """删除反馈"""
    result = db.query(UserFeedback).filter(UserFeedback.id == feedback_id).delete()
    db.commit()

    if result == 0:
        raise HTTPException(status_code=404, detail="反馈不存在")

    return {"message": "已删除"}
