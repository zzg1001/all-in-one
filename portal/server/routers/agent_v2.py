"""
Agent V2 API - 使用 Claude Agent SDK
用于测试和逐步迁移
"""

from fastapi import APIRouter, Depends, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from database import get_db
from services.agent_service_v2 import AgentServiceV2

router = APIRouter(prefix="/api/agent/v2", tags=["Agent V2 (SDK)"])


def get_user_id(x_user_id: Optional[str] = Header(None)) -> str:
    """获取用户ID"""
    return x_user_id or "anonymous"


# ============ 请求模型 ============

class ChatRequestV2(BaseModel):
    message: str
    skill_id: Optional[str] = None
    agent_id: Optional[str] = None  # 用于 RAG 数据隔离
    file_paths: Optional[List[str]] = None
    session_id: Optional[str] = None
    enable_rag: bool = True  # 是否启用 RAG 检索


class ExecuteSkillRequest(BaseModel):
    skill_id: str
    file_paths: List[str]


# ============ API 端点 ============

@router.post("/chat")
async def chat_v2(
    request: ChatRequestV2,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """
    非流式对话 (SDK 版本，支持 RAG)
    """
    service = AgentServiceV2(db)
    result = await service.chat(
        message=request.message,
        skill_id=request.skill_id,
        file_paths=request.file_paths,
        agent_id=request.agent_id,
        user_id=user_id,
        enable_rag=request.enable_rag
    )
    return result


@router.post("/chat/stream")
async def chat_stream_v2(
    request: ChatRequestV2,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """
    流式对话 (SDK 版本，支持 RAG)
    """
    service = AgentServiceV2(db)

    async def generate():
        async for chunk in service.chat_stream(
            message=request.message,
            skill_id=request.skill_id,
            file_paths=request.file_paths,
            session_id=request.session_id,
            agent_id=request.agent_id,
            user_id=user_id,
            enable_rag=request.enable_rag
        ):
            yield f"data: {chunk}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/execute")
async def execute_skill_v2(request: ExecuteSkillRequest, db: Session = Depends(get_db)):
    """
    直接执行技能 (SDK 版本)
    """
    service = AgentServiceV2(db)

    async def generate():
        async for chunk in service.execute_skill_direct(
            skill_id=request.skill_id,
            file_paths=request.file_paths
        ):
            yield f"data: {chunk}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/health")
async def health_check():
    """
    健康检查
    """
    try:
        from claude_agent_sdk import __version__
        return {
            "status": "ok",
            "sdk_version": __version__,
            "message": "Claude Agent SDK is ready"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
