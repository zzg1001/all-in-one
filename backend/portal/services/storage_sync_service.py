"""
Storage Sync Service - 启动时从 MinIO 同步文件到本地缓存

功能：
- 启动时预热本地缓存（从 MinIO 拉取 Skills 和 File Manage 文件）
- 只同步数据库中未删除的记录（检查 deleted_at 标签）
- 保证第一次访问也能直接读本地
- 支持强制同步（覆盖本地文件）和按文件大小检测更新
"""
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Set, Optional, List

from app.core.config import get_settings, get_skills_storage_dir, get_file_manage_dir
from portal.services.storage.utils import get_storage_backend, is_minio_storage


def get_active_skill_folders() -> Set[str]:
    """获取数据库中未删除的 Skill 文件夹列表"""
    from app.core.database import SessionLocal
    from portal.models.skill import Skill

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
    from app.core.database import SessionLocal
    from portal.models.data_note import DataNote

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


async def sync_minio_to_local(
    category: str,
    local_dir: Path,
    active_folders: Optional[Set[str]] = None,
    force: bool = False,
    check_size: bool = True
) -> int:
    """
    从 MinIO 同步文件到本地目录

    Args:
        category: 存储类别 ("skills", "file_manage")
        local_dir: 本地目录
        active_folders: 数据库中未删除的文件夹列表，None 表示同步所有
        force: 强制覆盖所有文件
        check_size: 检查文件大小，大小不同则更新

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

            # 判断是否需要下载
            need_download = False
            if not local_path.exists():
                need_download = True
            elif force:
                need_download = True
            elif check_size and hasattr(file_info, 'size') and file_info.size:
                # 比较文件大小
                local_size = local_path.stat().st_size
                if local_size != file_info.size:
                    need_download = True
                    print(f"[Sync] 文件大小变化 {remote_path}: 本地 {local_size} vs 远程 {file_info.size}")

            if not need_download:
                continue

            # 从 MinIO 下载
            try:
                content = await storage.read_file(remote_path)
                local_path.parent.mkdir(parents=True, exist_ok=True)
                local_path.write_bytes(content)
                synced_count += 1
                if force or (check_size and local_path.exists()):
                    print(f"[Sync] 更新文件: {remote_path}")
            except Exception as e:
                print(f"[Sync] 下载失败 {remote_path}: {e}")

        mode = "强制同步" if force else ("智能同步" if check_size else "增量同步")
        print(f"[Sync] {category}: {mode}完成，同步 {synced_count} 个文件")
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


async def sync_skill_from_minio(skill_folder: str, force: bool = True) -> dict:
    """
    从 MinIO 同步单个 Skill 到本地

    Args:
        skill_folder: Skill 的文件夹名（通常是 skill_id）
        force: 强制覆盖本地文件

    Returns:
        {"success": bool, "synced_files": int, "message": str}
    """
    if not is_minio_storage("skills"):
        return {"success": False, "synced_files": 0, "message": "Skills 未配置 MinIO 存储"}

    storage = get_storage_backend("skills")
    skills_dir = get_skills_storage_dir()
    synced_count = 0

    try:
        # 列出该 skill 文件夹下的所有文件
        prefix = f"{skill_folder}/"
        files = await storage.list_files(prefix, recursive=True)

        if not files:
            return {"success": False, "synced_files": 0, "message": f"MinIO 中未找到 skill: {skill_folder}"}

        for file_info in files:
            if file_info.is_dir:
                continue

            remote_path = file_info.path
            local_path = skills_dir / remote_path

            # 强制模式或文件不存在时下载
            if force or not local_path.exists():
                try:
                    content = await storage.read_file(remote_path)
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    local_path.write_bytes(content)
                    synced_count += 1
                    print(f"[Sync Skill] 同步文件: {remote_path}")
                except Exception as e:
                    print(f"[Sync Skill] 下载失败 {remote_path}: {e}")

        return {
            "success": True,
            "synced_files": synced_count,
            "message": f"成功同步 {synced_count} 个文件"
        }

    except Exception as e:
        return {"success": False, "synced_files": 0, "message": str(e)}


async def sync_skills_from_minio(skill_folders: List[str], force: bool = True) -> dict:
    """
    从 MinIO 同步多个 Skills 到本地

    Args:
        skill_folders: Skill 文件夹名列表
        force: 强制覆盖本地文件

    Returns:
        {"success": bool, "total_synced": int, "details": dict}
    """
    total_synced = 0
    details = {}

    for folder in skill_folders:
        result = await sync_skill_from_minio(folder, force)
        details[folder] = result
        if result["success"]:
            total_synced += result["synced_files"]

    return {
        "success": True,
        "total_synced": total_synced,
        "details": details
    }


def parse_skill_md(content: str) -> dict:
    """
    解析 SKILL.md 文件，提取 frontmatter 和标题

    支持的 frontmatter 格式（YAML）：
    ---
    name: 技能名称
    description: |
      技能描述
    output_config:
      enabled: true
      preferred_type: html
    ---

    Args:
        content: SKILL.md 文件内容

    Returns:
        解析后的元数据字典
    """
    import yaml
    import re

    result = {
        "name": None,
        "description": None,
        "icon": "⚡",
        "tags": [],
        "output_config": None,
        "entry_script": "main.py",
        "author": "minio_import",
        "version": "1.0.0"
    }

    # 解析 YAML frontmatter
    frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if frontmatter_match:
        try:
            frontmatter = yaml.safe_load(frontmatter_match.group(1))
            if frontmatter:
                result["name"] = frontmatter.get("name")
                result["description"] = frontmatter.get("description", "").strip() if frontmatter.get("description") else None
                result["icon"] = frontmatter.get("icon", "⚡")
                result["tags"] = frontmatter.get("tags", [])
                if frontmatter.get("output_config"):
                    result["output_config"] = frontmatter["output_config"]
        except yaml.YAMLError as e:
            print(f"[ParseSkillMD] YAML 解析错误: {e}")

    # 如果 frontmatter 中没有 name，从标题提取
    if not result["name"]:
        # 跳过 frontmatter 后的内容
        body = content
        if frontmatter_match:
            body = content[frontmatter_match.end():]

        # 查找第一个 # 标题
        title_match = re.search(r'^#\s+(.+)$', body, re.MULTILINE)
        if title_match:
            result["name"] = title_match.group(1).strip()

    # 如果还没有 description，从正文提取
    if not result["description"]:
        body = content
        if frontmatter_match:
            body = content[frontmatter_match.end():]

        # 跳过标题，找第一段非空文本
        lines = body.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('-'):
                result["description"] = line[:200]
                break

    return result


async def discover_and_import_skills_from_minio() -> dict:
    """
    从 MinIO 发现并导入新技能到数据库

    扫描 MinIO 中的所有技能文件夹，对于数据库中不存在的技能：
    1. 下载 SKILL.md 或 config.json
    2. 解析元数据
    3. 创建数据库记录
    4. 同步文件到本地

    Returns:
        {"success": bool, "imported": list, "skipped": list, "errors": list}
    """
    import json
    import uuid

    if not is_minio_storage("skills"):
        return {"success": False, "message": "Skills 未配置 MinIO 存储", "imported": [], "skipped": [], "errors": []}

    from app.core.database import SessionLocal
    from portal.models.skill import Skill

    storage = get_storage_backend("skills")
    skills_dir = get_skills_storage_dir()

    # 获取数据库中已存在的技能 folder_path
    db = SessionLocal()
    try:
        existing_folders = set()
        existing_skills = db.query(Skill.folder_path).filter(Skill.folder_path.isnot(None)).all()
        for s in existing_skills:
            if s.folder_path:
                existing_folders.add(s.folder_path)

        print(f"[DiscoverSkills] 数据库中已有 {len(existing_folders)} 个技能")

        # 列出 MinIO 根目录下的所有"文件夹"
        files = await storage.list_files("", recursive=False)
        minio_folders = set()
        for f in files:
            if f.is_dir:
                folder_name = f.name.rstrip('/')
                minio_folders.add(folder_name)
            elif '/' in f.path:
                # 从文件路径提取顶级文件夹
                folder_name = f.path.split('/')[0]
                minio_folders.add(folder_name)

        print(f"[DiscoverSkills] MinIO 中发现 {len(minio_folders)} 个技能文件夹")

        # 找出 MinIO 中有但数据库中没有的技能
        new_folders = minio_folders - existing_folders
        print(f"[DiscoverSkills] 需要导入 {len(new_folders)} 个新技能")

        imported = []
        skipped = []
        errors = []

        for folder in new_folders:
            try:
                print(f"[DiscoverSkills] 处理: {folder}")

                # 尝试读取 SKILL.md
                skill_info = None
                try:
                    skill_md_content = await storage.read_file_text(f"{folder}/SKILL.md")
                    skill_info = parse_skill_md(skill_md_content)
                    print(f"[DiscoverSkills] 从 SKILL.md 解析: name={skill_info.get('name')}")
                except FileNotFoundError:
                    print(f"[DiscoverSkills] {folder}/SKILL.md 不存在，尝试 config.json")

                # 如果没有 SKILL.md，尝试 config.json
                if not skill_info or not skill_info.get("name"):
                    try:
                        config_content = await storage.read_file_text(f"{folder}/config.json")
                        config = json.loads(config_content)
                        skill_info = {
                            "name": config.get("name", folder),
                            "description": config.get("description"),
                            "icon": config.get("icon", "⚡"),
                            "tags": config.get("tags", []),
                            "output_config": config.get("output_config"),
                            "entry_script": config.get("entry_script", "main.py"),
                            "author": config.get("author", "minio_import"),
                            "version": config.get("version", "1.0.0")
                        }
                        print(f"[DiscoverSkills] 从 config.json 解析: name={skill_info.get('name')}")
                    except FileNotFoundError:
                        print(f"[DiscoverSkills] {folder}/config.json 也不存在")
                        skill_info = {
                            "name": folder,
                            "description": None,
                            "icon": "⚡",
                            "tags": [],
                            "output_config": None,
                            "entry_script": "main.py",
                            "author": "minio_import",
                            "version": "1.0.0"
                        }

                if not skill_info.get("name"):
                    skill_info["name"] = folder

                # 检查入口脚本是否存在
                entry_script = skill_info.get("entry_script", "main.py")
                try:
                    await storage.read_file(f"{folder}/{entry_script}")
                except FileNotFoundError:
                    # 尝试找其他 .py 文件
                    folder_files = await storage.list_files(f"{folder}/", recursive=False)
                    py_files = [f.name for f in folder_files if f.name.endswith('.py') and not f.is_dir]
                    if py_files:
                        entry_script = py_files[0]
                    else:
                        entry_script = None

                # 创建数据库记录
                skill = Skill(
                    id=folder,  # 使用 MinIO 中的文件夹名作为 ID
                    group_id=folder,
                    name=skill_info["name"],
                    description=skill_info.get("description"),
                    icon=skill_info.get("icon", "⚡"),
                    tags=skill_info.get("tags", []),
                    folder_path=folder,
                    entry_script=entry_script,
                    author=skill_info.get("author", "minio_import"),
                    version=skill_info.get("version", "1.0.0"),
                    status="active",
                    output_config=skill_info.get("output_config"),
                    minio_synced=True  # 来自 MinIO，已同步
                )

                db.add(skill)
                db.commit()
                print(f"[DiscoverSkills] 数据库记录已创建: {skill_info['name']} ({folder})")

                # 同步文件到本地
                sync_result = await sync_skill_from_minio(folder, force=True)
                print(f"[DiscoverSkills] 文件同步完成: {sync_result['synced_files']} 个文件")

                imported.append({
                    "folder": folder,
                    "name": skill_info["name"],
                    "synced_files": sync_result["synced_files"]
                })

            except Exception as e:
                import traceback
                traceback.print_exc()
                errors.append({
                    "folder": folder,
                    "error": str(e)
                })

        return {
            "success": True,
            "message": f"导入完成: {len(imported)} 成功, {len(skipped)} 跳过, {len(errors)} 错误",
            "imported": imported,
            "skipped": list(existing_folders & minio_folders),
            "errors": errors
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "message": str(e), "imported": [], "skipped": [], "errors": []}
    finally:
        db.close()
