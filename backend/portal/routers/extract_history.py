"""
企业信息提取 - 历史记录路由（保存/列表/编辑/删除/下载）

记录全局共享（不按用户隔离），软删除。
"""
import uuid
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from app.core.database import get_db
from portal.models.extract_record import ExtractRecord
from portal.schemas.extract_record import (
    ExtractRecordCreate,
    ExtractRecordUpdate,
    ExtractRecordResponse,
    BatchDeleteRequest,
)
from portal.services.extract_service import ExtractService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/extract/records", tags=["Portal - Extract"])


def get_user_id(x_user_id: Optional[str] = Header(None)) -> str:
    """从请求头 X-User-ID 获取用户ID，缺省 anonymous"""
    return x_user_id or "anonymous"


def _company_name_of(data: dict) -> str:
    return (data or {}).get("企业名称") or ""


def _credit_code_of(data: dict) -> str:
    d = data or {}
    return d.get("统一社会信用代码") or d.get("统一社会信用码") or ""


@router.get("", response_model=list[ExtractRecordResponse])
async def list_records(db: Session = Depends(get_db)):
    """列出所有未删除的记录（全局共享，按保存时间倒序）"""
    records = db.query(ExtractRecord).filter(
        ExtractRecord.deleted_at.is_(None)
    ).order_by(ExtractRecord.created_at.desc()).all()
    return records


@router.get("/{record_id}", response_model=ExtractRecordResponse)
async def get_record(record_id: str, db: Session = Depends(get_db)):
    """获取单条记录"""
    record = db.query(ExtractRecord).filter(
        ExtractRecord.id == record_id,
        ExtractRecord.deleted_at.is_(None)
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    return record


@router.post("", response_model=ExtractRecordResponse)
async def create_record(
    payload: ExtractRecordCreate,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    """保存一条企业信息提取记录"""
    record = ExtractRecord(
        id=str(uuid.uuid4()),
        user_id=user_id,
        company_name=payload.company_name or _company_name_of(payload.data),
        credit_code=payload.credit_code or _credit_code_of(payload.data),
        data=payload.data,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.put("/{record_id}", response_model=ExtractRecordResponse)
async def update_record(
    record_id: str,
    payload: ExtractRecordUpdate,
    db: Session = Depends(get_db),
):
    """编辑后更新记录"""
    record = db.query(ExtractRecord).filter(
        ExtractRecord.id == record_id,
        ExtractRecord.deleted_at.is_(None)
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")

    updates = payload.model_dump(exclude_unset=True)
    if "data" in updates and updates["data"] is not None:
        record.data = updates["data"]
        # data 变了，同步派生字段
        record.company_name = updates.get("company_name") or _company_name_of(updates["data"])
        record.credit_code = updates.get("credit_code") or _credit_code_of(updates["data"])
    else:
        if "company_name" in updates:
            record.company_name = updates["company_name"]
        if "credit_code" in updates:
            record.credit_code = updates["credit_code"]

    db.commit()
    db.refresh(record)
    return record


@router.post("/batch-delete")
async def batch_delete_records(
    payload: BatchDeleteRequest,
    db: Session = Depends(get_db),
):
    """批量软删除"""
    if not payload.ids:
        return {"deleted": 0}
    now = datetime.now()
    count = db.query(ExtractRecord).filter(
        ExtractRecord.id.in_(payload.ids),
        ExtractRecord.deleted_at.is_(None)
    ).update({ExtractRecord.deleted_at: now}, synchronize_session=False)
    db.commit()
    return {"deleted": count}


@router.delete("/{record_id}")
async def delete_record(record_id: str, db: Session = Depends(get_db)):
    """单条软删除"""
    record = db.query(ExtractRecord).filter(
        ExtractRecord.id == record_id,
        ExtractRecord.deleted_at.is_(None)
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    record.deleted_at = datetime.now()
    db.commit()
    return {"message": "已删除"}


@router.post("/{record_id}/word")
async def download_record_word(record_id: str, db: Session = Depends(get_db)):
    """用记录数据重新生成 Word，返回 base64"""
    record = db.query(ExtractRecord).filter(
        ExtractRecord.id == record_id,
        ExtractRecord.deleted_at.is_(None)
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    try:
        service = ExtractService()
        word_base64 = service.generate_word(record.data or {})
        return {"success": True, "word_file_base64": word_base64}
    except Exception as e:
        logger.error(f"生成 Word 文档失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")
