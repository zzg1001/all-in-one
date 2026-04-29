"""
Dashboard API - 驾驶舱数据
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
from typing import List

from app.core.database import get_db
from portal.models.chat import ChatSession, ChatMessage
from portal.models.agent import Agent, AgentExecution
from portal.models.skill import Skill
from portal.models.feedback import UserFeedback

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """获取驾驶舱统计数据"""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)

    # 今日会话数
    today_sessions = db.query(func.count(ChatSession.id)).filter(
        ChatSession.created_at >= today
    ).scalar() or 0

    # 昨日会话数（用于计算增长）
    yesterday_sessions = db.query(func.count(ChatSession.id)).filter(
        and_(ChatSession.created_at >= yesterday, ChatSession.created_at < today)
    ).scalar() or 0

    # 今日消息数
    today_messages = db.query(func.count(ChatMessage.id)).filter(
        ChatMessage.created_at >= today
    ).scalar() or 0

    # 总会话数
    total_sessions = db.query(func.count(ChatSession.id)).scalar() or 0

    # 总消息数
    total_messages = db.query(func.count(ChatMessage.id)).scalar() or 0

    # 活跃用户数（过去7天有会话的用户）
    active_users = db.query(func.count(func.distinct(ChatSession.user_id))).filter(
        ChatSession.created_at >= week_ago
    ).scalar() or 0

    # Agent 执行统计
    today_executions = db.query(func.count(AgentExecution.id)).filter(
        AgentExecution.created_at >= today
    ).scalar() or 0

    # Token 统计（今日）
    today_tokens = db.query(func.sum(AgentExecution.total_tokens)).filter(
        AgentExecution.created_at >= today
    ).scalar() or 0

    # 总 Token 使用量
    total_tokens = db.query(func.sum(AgentExecution.total_tokens)).scalar() or 0

    # 成功率（今日执行）
    today_success = db.query(func.count(AgentExecution.id)).filter(
        and_(AgentExecution.created_at >= today, AgentExecution.status == 'completed')
    ).scalar() or 0
    success_rate = round((today_success / today_executions * 100) if today_executions > 0 else 100, 1)

    # 平均延迟（今日，毫秒）
    avg_latency = db.query(func.avg(AgentExecution.latency_ms)).filter(
        and_(AgentExecution.created_at >= today, AgentExecution.latency_ms.isnot(None))
    ).scalar() or 0

    # 技能数量
    skill_count = db.query(func.count(Skill.id)).filter(
        and_(Skill.status == 'active', Skill.deleted_at.is_(None))
    ).scalar() or 0

    # Agent 数量
    agent_count = db.query(func.count(Agent.id)).filter(
        Agent.status == 'active'
    ).scalar() or 0

    # 反馈统计
    pending_feedbacks = db.query(func.count(UserFeedback.id)).filter(
        UserFeedback.status == 'pending'
    ).scalar() or 0

    total_feedbacks = db.query(func.count(UserFeedback.id)).scalar() or 0

    # 计算增长率
    session_growth = round(((today_sessions - yesterday_sessions) / yesterday_sessions * 100) if yesterday_sessions > 0 else 0, 1)

    return {
        "today_sessions": today_sessions,
        "today_messages": today_messages,
        "today_executions": today_executions,
        "today_tokens": today_tokens,
        "total_sessions": total_sessions,
        "total_messages": total_messages,
        "total_tokens": total_tokens,
        "active_users": active_users,
        "success_rate": success_rate,
        "avg_latency": round(avg_latency, 0),
        "skill_count": skill_count,
        "agent_count": agent_count,
        "pending_feedbacks": pending_feedbacks,
        "total_feedbacks": total_feedbacks,
        "session_growth": session_growth,
    }


@router.get("/trends")
async def get_trends(days: int = 7, db: Session = Depends(get_db)):
    """获取趋势数据"""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    dates = []
    sessions = []
    messages = []
    executions = []
    tokens = []

    for i in range(days - 1, -1, -1):
        day_start = today - timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        dates.append(day_start.strftime("%m-%d"))

        # 会话数
        day_sessions = db.query(func.count(ChatSession.id)).filter(
            and_(ChatSession.created_at >= day_start, ChatSession.created_at < day_end)
        ).scalar() or 0
        sessions.append(day_sessions)

        # 消息数
        day_messages = db.query(func.count(ChatMessage.id)).filter(
            and_(ChatMessage.created_at >= day_start, ChatMessage.created_at < day_end)
        ).scalar() or 0
        messages.append(day_messages)

        # 执行数
        day_executions = db.query(func.count(AgentExecution.id)).filter(
            and_(AgentExecution.created_at >= day_start, AgentExecution.created_at < day_end)
        ).scalar() or 0
        executions.append(day_executions)

        # Token数
        day_tokens = db.query(func.sum(AgentExecution.total_tokens)).filter(
            and_(AgentExecution.created_at >= day_start, AgentExecution.created_at < day_end)
        ).scalar() or 0
        tokens.append(day_tokens)

    return {
        "dates": dates,
        "sessions": sessions,
        "messages": messages,
        "executions": executions,
        "tokens": tokens,
    }


@router.get("/recent-feedbacks")
async def get_recent_feedbacks(limit: int = 5, db: Session = Depends(get_db)):
    """获取最近的反馈"""
    feedbacks = db.query(UserFeedback).order_by(
        UserFeedback.created_at.desc()
    ).limit(limit).all()

    return [
        {
            "id": f.id,
            "title": f.title,
            "feedback_type": f.feedback_type,
            "status": f.status,
            "agent_name": f.agent_name,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in feedbacks
    ]


@router.get("/top-agents")
async def get_top_agents(limit: int = 5, db: Session = Depends(get_db)):
    """获取使用量最高的 Agent"""
    agents = db.query(Agent).filter(
        Agent.status == 'active'
    ).order_by(Agent.usage_count.desc()).limit(limit).all()

    return [
        {
            "id": a.id,
            "name": a.name,
            "icon": a.icon,
            "category": a.category,
            "usage_count": a.usage_count,
        }
        for a in agents
    ]
