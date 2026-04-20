"""
Dashboard API - 驾驶舱数据
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from datetime import datetime, timedelta

from app.core.database import get_db

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """获取驾驶舱统计数据"""
    # TODO: 实现实际的统计逻辑
    return {
        "today_calls": 0,
        "today_tokens": 0,
        "active_users": 0,
        "success_rate": 100.0,
    }


@router.get("/trends")
async def get_trends(days: int = 7, db: Session = Depends(get_db)):
    """获取趋势数据"""
    # TODO: 实现实际的趋势查询
    dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days - 1, -1, -1)]
    return {
        "dates": dates,
        "calls": [0] * days,
        "tokens": [0] * days,
    }
