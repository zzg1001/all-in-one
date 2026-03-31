"""
Cleanup Service - 定期清理软删除的数据和物理文件

清理逻辑：deleted_at 不为空就删除（不管时间）

使用方式：
1. 手动执行: python scripts/cleanup.py
2. 定时任务: 服务启动时自动注册（每天执行一次）

配置（deploy.env）:
    CLEANUP_INTERVAL_HOURS=24    # 执行间隔（小时）
"""
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Tuple
from sqlalchemy.orm import Session

from database import SessionLocal
from models.data_note import DataNote
from models.skill import Skill
from config import get_settings, get_uploads_dir, get_outputs_dir, get_skills_storage_dir, get_file_manage_dir


def get_cleanup_interval_hours() -> int:
    """从配置获取清理间隔"""
    return get_settings().cleanup_interval_hours


async def cleanup_deleted_data_notes(db: Session) -> Tuple[int, int]:
    """
    清理软删除的 DataNote 记录及其物理文件

    只要 deleted_at 不为空就删除，不管时间

    Returns:
        (deleted_records, deleted_files) 删除的记录数和文件数
    """
    from services.storage.utils import get_storage_backend, is_minio_storage

    # 查询需要清理的记录（deleted_at 不为空）
    notes_to_delete = db.query(DataNote).filter(
        DataNote.deleted_at.isnot(None)
    ).all()

    if not notes_to_delete:
        print(f"[Cleanup] DataNotes: 没有需要清理的记录")
        return 0, 0

    deleted_records = 0
    deleted_files = 0
    uploads_dir = get_uploads_dir()
    file_manage_dir = get_file_manage_dir()  # File Manage 独立目录
    outputs_dir = get_outputs_dir()

    for note in notes_to_delete:
        # 删除物理文件
        if note.file_url and note.file_type != 'folder':
            try:
                # 解析路径
                if note.file_url.startswith('/file-manage/'):
                    relative_path = note.file_url[len('/file-manage/'):]
                    local_path = file_manage_dir / relative_path  # 使用独立的 file_manage 目录
                    category = "file_manage"
                elif note.file_url.startswith('/uploads/'):
                    relative_path = note.file_url[len('/uploads/'):]
                    local_path = uploads_dir / relative_path
                    category = "uploads"
                elif note.file_url.startswith('/outputs/'):
                    relative_path = note.file_url[len('/outputs/'):]
                    local_path = outputs_dir / relative_path
                    category = "outputs"
                else:
                    relative_path = None
                    local_path = None
                    category = None

                if local_path and local_path.exists():
                    local_path.unlink()
                    deleted_files += 1
                    print(f"[Cleanup] 删除本地文件: {local_path}")

                # 删除 MinIO 文件
                if category and is_minio_storage(category):
                    storage = get_storage_backend(category)
                    try:
                        await storage.delete_file(relative_path)
                        print(f"[Cleanup] 删除 MinIO 文件: {category}/{relative_path}")
                    except Exception as e:
                        print(f"[Cleanup] MinIO 删除失败: {e}")

            except Exception as e:
                print(f"[Cleanup] 文件删除失败 ({note.file_url}): {e}")

        # 删除向量索引
        try:
            from routers.data_notes import get_vector_service
            vector_service = get_vector_service()
            if vector_service:
                await vector_service.delete_file_index(note.id)
        except Exception as e:
            print(f"[Cleanup] 向量索引删除失败: {e}")

        # 删除数据库记录
        db.delete(note)
        deleted_records += 1

    db.commit()
    print(f"[Cleanup] DataNotes: 清理完成，删除 {deleted_records} 条记录，{deleted_files} 个文件")
    return deleted_records, deleted_files


async def cleanup_deleted_skills(db: Session) -> Tuple[int, int]:
    """
    清理软删除的 Skill 记录及其文件夹

    只要 deleted_at 不为空就删除，不管时间

    Returns:
        (deleted_records, deleted_folders) 删除的记录数和文件夹数
    """
    from services.storage.utils import delete_skill_folder_from_storage

    skills_dir = get_skills_storage_dir()

    # 查询需要清理的记录（deleted_at 不为空）
    skills_to_delete = db.query(Skill).filter(
        Skill.deleted_at.isnot(None)
    ).all()

    if not skills_to_delete:
        print(f"[Cleanup] Skills: 没有需要清理的记录")
        return 0, 0

    deleted_records = 0
    deleted_folders = 0

    for skill in skills_to_delete:
        # 删除文件夹（本地 + MinIO）
        if skill.folder_path:
            try:
                skill_folder = skills_dir / skill.folder_path
                await delete_skill_folder_from_storage(skill.folder_path, skill_folder)
                deleted_folders += 1
            except Exception as e:
                print(f"[Cleanup] 文件夹删除失败 ({skill.folder_path}): {e}")

        # 删除数据库记录
        db.delete(skill)
        deleted_records += 1

    db.commit()
    print(f"[Cleanup] Skills: 清理完成，删除 {deleted_records} 条记录，{deleted_folders} 个文件夹")
    return deleted_records, deleted_folders


async def run_cleanup():
    """
    执行完整的清理任务

    清理所有 deleted_at 不为空的记录
    """
    print(f"\n{'='*60}")
    print(f"[Cleanup] 开始清理任务 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[Cleanup] 清理所有已标记删除的数据")
    print(f"{'='*60}\n")

    db = SessionLocal()
    try:
        # 清理 DataNotes
        notes_records, notes_files = await cleanup_deleted_data_notes(db)

        # 清理 Skills
        skills_records, skills_folders = await cleanup_deleted_skills(db)

        print(f"\n{'='*60}")
        print(f"[Cleanup] 清理完成!")
        print(f"  - DataNotes: {notes_records} 条记录, {notes_files} 个文件")
        print(f"  - Skills: {skills_records} 条记录, {skills_folders} 个文件夹")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"[Cleanup] 清理失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


# ============ 后台任务调度 ============

_cleanup_task = None


async def start_cleanup_scheduler(interval_hours: int = None):
    """
    启动后台清理调度器

    Args:
        interval_hours: 执行间隔（小时），默认从配置读取
    """
    global _cleanup_task

    # 从配置读取默认值
    if interval_hours is None:
        interval_hours = get_cleanup_interval_hours()

    async def scheduler():
        # 首次启动延迟1小时执行（避免启动时立即清理）
        await asyncio.sleep(3600)
        while True:
            try:
                await run_cleanup()
            except Exception as e:
                print(f"[Cleanup Scheduler] 执行失败: {e}")
            await asyncio.sleep(interval_hours * 3600)

    _cleanup_task = asyncio.create_task(scheduler())
    print(f"[Cleanup Scheduler] 已启动，每 {interval_hours} 小时执行一次")


def stop_cleanup_scheduler():
    """停止后台清理调度器"""
    global _cleanup_task
    if _cleanup_task:
        _cleanup_task.cancel()
        _cleanup_task = None
        print("[Cleanup Scheduler] 已停止")


# ============ 命令行入口 ============

if __name__ == "__main__":
    print("清理所有已标记删除的数据（deleted_at 不为空）")
    asyncio.run(run_cleanup())
