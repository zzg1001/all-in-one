"""
Tokens API - Token 用量统计
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from app.core.database import get_db

router = APIRouter()


@router.get("/summary")
async def get_token_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取 Token 使用汇总"""
    # TODO: 实现实际的统计逻辑
    return {
        "total_tokens": 0,
        "total_cost": 0.0,
        "by_user": [],
        "by_skill": [],
        "by_date": [],
    }


@router.get("/usage")
async def get_token_usage(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    user_id: Optional[str] = None,
    skill_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取 Token 使用明细"""
    # TODO: 从数据库查询
    return {
        "items": [],
        "total": 0,
        "page": page,
        "limit": limit,
    }


@router.get("/quotas")
async def get_quotas(db: Session = Depends(get_db)):
    """获取配额设置"""
    return {
        "global_daily_limit": None,
        "global_monthly_limit": None,
        "user_quotas": [],
    }


@router.put("/quotas")
async def update_quotas(data: dict, db: Session = Depends(get_db)):
    """更新配额设置"""
    # TODO: 保存配额设置
    return {"message": "Quotas updated"}
