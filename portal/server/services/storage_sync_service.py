"""
Storage Sync Service - 启动时从 MinIO 同步文件到本地缓存

功能：
- 启动时预热本地缓存（从 MinIO 拉取 Skills 和 File Manage 文件）
- 只同步数据库中未删除的记录（检查 deleted_at 标签）
- 保证第一次访问也能直接读本地
"""
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Set, Optional

from config import get_settings, get_skills_storage_dir, get_file_manage_dir
from services.storage.utils import get_storage_backend, is_minio_storage


def get_active_skill_folders() -> Set[str]:
    """获取数据库中未删除的 Skill 文件夹列表"""
    from database import SessionLocal
    from models.skill import Skill

    db = SessionLocal()
    try:
        skills = db.query(Skill.folder_path).filter(
            Skill.deleted_at.is_(None),
            Skill.folder_path.isnot(None)
        ).all()
        return {s.folder_path for s in skills if s.folder_path}
    finally:
        db.close()


def get_active_file_manage_folders() -> Set[str]:
    """获取数据库中未删除的 File Manage 文件夹列表（按 agent_id）"""
    from database import SessionLocal
    from models.data_note import DataNote

    db = SessionLocal()
    try:
        # 获取所有未删除记录的 agent_id
        notes = db.query(DataNote.agent_id).filter(
            DataNote.deleted_at.is_(None),
            DataNote.agent_id.isnot(None)
        ).distinct().all()
        return {n.agent_id for n in notes if n.agent_id}
    finally:
        db.close()


async def sync_minio_to_local(category: str, local_dir: Path, active_folders: Optional[Set[str]] = None) -> int:
    """
    从 MinIO 增量同步文件到本地目录（只同步本地不存在的文件）

    Args:
        category: 存储类别 ("skills", "file_manage")
        local_dir: 本地目录
        active_folders: 数据库中未删除的文件夹列表，None 表示同步所有

    Returns:
        同步的文件数量
    """
    if not is_minio_storage(category):
        print(f"[Sync] {category} 未配置 MinIO，跳过")
        return 0

    storage = get_storage_backend(category)
    synced_count = 0

    try:
        # 确保本地目录存在
        local_dir.mkdir(parents=True, exist_ok=True)

        # 列出 MinIO 中的所有文件
        files = await storage.list_files("", recursive=True)

        for file_info in files:
            if file_info.is_dir:
                continue

            remote_path = file_info.path

            # 检查是否在活跃文件夹列表中
            if active_folders is not None:
                # 获取顶级文件夹名（skill_id 或 agent_id）
                top_folder = remote_path.split('/')[0] if '/' in remote_path else remote_path
                if top_folder not in active_folders:
                    continue  # 跳过已删除的文件夹

            local_path = local_dir / remote_path

            # 只下载本地不存在的文件（增量同步）
            if local_path.exists():
                continue

            # 从 MinIO 下载
            try:
                content = await storage.read_file(remote_path)
                local_path.parent.mkdir(parents=True, exist_ok=True)
                local_path.write_bytes(content)
                synced_count += 1
            except Exception as e:
                print(f"[Sync] 下载失败 {remote_path}: {e}")

        print(f"[Sync] {category}: 增量同步完成，新增 {synced_count} 个文件")
        return synced_count

    except Exception as e:
        print(f"[Sync] {category} 同步失败: {e}")
        return 0


async def sync_all_on_startup():
    """
    启动时同步所有需要共享的存储（只同步数据库中未删除的记录）
    """
    print(f"\n{'='*60}")
    print(f"[Sync] 开始同步 MinIO → 本地缓存")
    print(f"[Sync] 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    settings = get_settings()
    total_synced = 0

    # 获取数据库中未删除的文件夹列表
    active_skills = get_active_skill_folders()
    active_file_manage = get_active_file_manage_folders()
    print(f"[Sync] 活跃 Skills: {len(active_skills)} 个")
    print(f"[Sync] 活跃 File Manage agents: {len(active_file_manage)} 个")

    # 同步 Skills（只同步未删除的）
    skills_dir = get_skills_storage_dir()
    skills_count = await sync_minio_to_local("skills", skills_dir, active_skills)
    total_synced += skills_count

    # 同步 File Manage（只同步未删除的）
    file_manage_dir = get_file_manage_dir()
    file_manage_count = await sync_minio_to_local("file_manage", file_manage_dir, active_file_manage)
    total_synced += file_manage_count

    print(f"\n{'='*60}")
    print(f"[Sync] 同步完成!")
    print(f"  - Skills: {skills_count} 个文件")
    print(f"  - File Manage: {file_manage_count} 个文件")
    print(f"  - 总计: {total_synced} 个文件")
    print(f"{'='*60}\n")

    return total_synced


# 后台同步任务（可选，定期同步）
_sync_task = None


async def start_periodic_sync(interval_minutes: int = 30):
    """
    启动定期同步任务

    Args:
        interval_minutes: 同步间隔（分钟）
    """
    global _sync_task

    async def sync_loop():
        while True:
            await asyncio.sleep(interval_minutes * 60)
            try:
                await sync_all_on_startup()
            except Exception as e:
                print(f"[Sync] 定期同步失败: {e}")

    _sync_task = asyncio.create_task(sync_loop())
    print(f"[Sync] 定期同步已启动，间隔 {interval_minutes} 分钟")


def stop_periodic_sync():
    """停止定期同步"""
    global _sync_task
    if _sync_task:
        _sync_task.cancel()
        _sync_task = None
        print("[Sync] 定期同步已停止")
