import uuid
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
from database import get_db
from models.chat import ChatSession, ChatMessage
from schemas.chat import (
    SessionCreate, SessionUpdate, SessionResponse, SessionWithMessages,
    MessageCreate, MessageResponse, SessionListResponse
)

router = APIRouter(prefix="/api/sessions", tags=["Chat Sessions"])


def get_user_id(x_user_id: Optional[str] = Header(None)) -> str:
    """获取用户ID"""
    if x_user_id:
        return x_user_id
    return "default"


def extract_title(content: str, max_length: int = 50) -> str:
    """从消息内容提取标题"""
    # 移除换行符，取第一行
    first_line = content.split('\n')[0].strip()
    if len(first_line) > max_length:
        return first_line[:max_length - 3] + "..."
    return first_line if first_line else "新对话"


# ============ 会话 API ============

@router.get("", response_model=SessionListResponse)
async def list_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: Optional[str] = None,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """获取会话列表"""
    query = db.query(ChatSession).filter(ChatSession.user_id == user_id)

    # 搜索
    if q and q.strip():
        query = query.filter(ChatSession.title.ilike(f"%{q}%"))

    # 总数
    total = query.count()

    # 分页 + 排序（最近更新的在前）
    sessions = query.order_by(desc(ChatSession.last_message_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return SessionListResponse(sessions=sessions, total=total)


@router.post("", response_model=SessionResponse)
async def create_session(
    data: SessionCreate,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """创建新会话"""
    session = ChatSession(
        id=str(uuid.uuid4()),
        user_id=user_id,
        title=data.title or "新对话",
        message_count=0,
        last_message_at=datetime.now()
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/{session_id}", response_model=SessionWithMessages)
async def get_session(
    session_id: str,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """获取会话详情（含所有消息）"""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == user_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 获取消息
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at).all()

    return SessionWithMessages(
        **{c.name: getattr(session, c.name) for c in session.__table__.columns},
        messages=[MessageResponse.from_orm_model(m) for m in messages]
    )


@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    data: SessionUpdate,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """更新会话（重命名）"""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == user_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if data.title is not None:
        session.title = data.title

    db.commit()
    db.refresh(session)
    return session


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """删除会话及其所有消息"""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == user_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 删除消息
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()

    # 删除会话
    db.delete(session)
    db.commit()

    return {"message": "Session deleted"}


# ============ 消息 API ============

@router.post("/{session_id}/messages", response_model=MessageResponse)
async def add_message(
    session_id: str,
    data: MessageCreate,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """添加消息到会话"""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == user_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 创建消息
    message = ChatMessage(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role=data.role,
        content=data.content,
        extra_data=data.metadata,
        created_at=data.created_at or datetime.now()  # 使用前端时间戳或当前时间
    )
    db.add(message)

    # 更新会话
    session.message_count += 1
    session.last_message_at = datetime.now()

    # 如果是第一条用户消息，自动设置标题
    if session.message_count == 1 and data.role == "user":
        session.title = extract_title(data.content)

    # 从 metadata 提取技能名称并更新会话
    if data.metadata and data.metadata.get("skill_plan"):
        skill_plan = data.metadata["skill_plan"]
        new_skills = [s.get("skillName") or s.get("skill_name") for s in skill_plan if s]
        new_skills = [s for s in new_skills if s]  # 过滤空值
        if new_skills:
            existing = session.skill_names or []
            # 合并去重
            session.skill_names = list(dict.fromkeys(existing + new_skills))

    db.commit()
    db.refresh(message)
    return MessageResponse.from_orm_model(message)


@router.get("/{session_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    session_id: str,
    limit: int = Query(100, ge=1, le=500),
    before_id: Optional[str] = None,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """获取会话消息（分页）"""
    # 验证会话归属
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == user_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    query = db.query(ChatMessage).filter(ChatMessage.session_id == session_id)

    # 游标分页
    if before_id:
        before_msg = db.query(ChatMessage).filter(ChatMessage.id == before_id).first()
        if before_msg:
            query = query.filter(ChatMessage.created_at < before_msg.created_at)

    messages = query.order_by(desc(ChatMessage.created_at)).limit(limit).all()

    # 返回时按时间正序
    return [MessageResponse.from_orm_model(m) for m in reversed(messages)]
