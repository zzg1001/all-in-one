"""
Cleanup API routes.
用于手动触发清理任务和查看清理状态。
"""
from fastapi import APIRouter, Query
from datetime import datetime, timedelta
from database import SessionLocal
from models.data_note import DataNote
from models.skill import Skill

router = APIRouter(prefix="/api/cleanup", tags=["cleanup"])


@router.get("/stats")
async def get_cleanup_stats():
    """获取待清理数据统计"""
    db = SessionLocal()
    try:
        # 统计软删除的记录
        deleted_notes = db.query(DataNote).filter(
            DataNote.deleted_at.isnot(None)
        ).count()

        deleted_skills = db.query(Skill).filter(
            Skill.deleted_at.isnot(None)
        ).count()

        # 统计 7 天前的（可以被清理的）
        cutoff = datetime.now() - timedelta(days=7)
        ready_notes = db.query(DataNote).filter(
            DataNote.deleted_at.isnot(None),
            DataNote.deleted_at < cutoff
        ).count()

        ready_skills = db.query(Skill).filter(
            Skill.deleted_at.isnot(None),
            Skill.deleted_at < cutoff
        ).count()

        return {
            "soft_deleted": {
                "data_notes": deleted_notes,
                "skills": deleted_skills,
                "total": deleted_notes + deleted_skills
            },
            "ready_to_cleanup": {
                "data_notes": ready_notes,
                "skills": ready_skills,
                "total": ready_notes + ready_skills
            },
            "retention_days": 7
        }
    finally:
        db.close()


@router.post("/run")
async def run_cleanup(retention_days: int = Query(default=7, ge=0, le=365)):
    """
    手动执行清理任务

    Args:
        retention_days: 保留天数（0 = 立即清理所有软删除的数据）
    """
    from services.cleanup_service import run_cleanup as do_cleanup

    await do_cleanup(retention_days)

    return {
        "status": "completed",
        "retention_days": retention_days,
        "message": f"清理完成，已删除 {retention_days} 天前软删除的数据"
    }


@router.delete("/force/{note_id}")
async def force_delete_note(note_id: str):
    """强制立即删除指定的 DataNote（包括物理文件）"""
    from services.cleanup_service import cleanup_deleted_data_notes
    from datetime import datetime

    db = SessionLocal()
    try:
        note = db.query(DataNote).filter(DataNote.id == note_id).first()
        if not note:
            return {"error": "记录不存在"}

        # 先标记为软删除
        if not note.deleted_at:
            note.deleted_at = datetime.now()
            db.commit()

        # 立即执行清理（retention_days=0 立即清理）
        # 只清理这一条记录
        note.deleted_at = datetime.now() - timedelta(days=100)  # 设置为很久以前
        db.commit()

        records, files = await cleanup_deleted_data_notes(db, retention_days=0)

        return {
            "status": "deleted",
            "note_id": note_id,
            "deleted_files": files
        }
    finally:
        db.close()
