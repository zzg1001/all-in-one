"""
Storage utility functions.
Provides helpers for syncing local files to configured storage backend.
Supports category-based storage: skills → MinIO, uploads/outputs → local (configurable).
"""
import os
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, Literal
from datetime import datetime
import mimetypes


StorageCategory = Literal["skills", "file_manage", "uploads", "outputs"]


def get_storage_backend(category: StorageCategory = "outputs"):
    """Get the configured storage backend for a category.

    Args:
        category: "skills", "file_manage", "uploads", or "outputs"
            - skills: 技能文件（MinIO 共享）
            - file_manage: File Manage 文件（MinIO 共享）
            - uploads: 输入框临时上传（本地）
            - outputs: 输出文件（本地）

    Returns:
        Storage backend instance (MinioStorage or LocalStorage)
    """
    from config import get_settings, get_outputs_dir, get_uploads_dir, get_file_manage_dir, get_skills_storage_dir
    settings = get_settings()

    storage_type = settings.get_storage_type_for(category)

    if storage_type == "minio":
        from services.storage.minio_storage import MinioStorage

        # 根据类别选择 bucket
        bucket_map = {
            "skills": settings.minio_skills_bucket,
            "file_manage": settings.minio_file_manage_bucket,
            "uploads": settings.minio_uploads_bucket,
            "outputs": settings.minio_outputs_bucket,
        }
        bucket = bucket_map.get(category, settings.minio_default_bucket)

        return MinioStorage(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            bucket=bucket,
            port=settings.minio_port,
            secure=settings.minio_secure
        )
    else:
        from services.storage.local import LocalStorage

        # 根据类别选择本地目录
        dir_map = {
            "skills": str(get_skills_storage_dir()),
            "file_manage": str(get_file_manage_dir()),  # File Manage 独立目录
            "uploads": str(get_uploads_dir()),
            "outputs": str(get_outputs_dir()),
        }
        base_dir = dir_map.get(category, str(get_outputs_dir()))

        return LocalStorage(base_dir)


def is_minio_storage(category: StorageCategory) -> bool:
    """Check if a category uses MinIO storage."""
    from config import get_settings
    settings = get_settings()
    return settings.get_storage_type_for(category) == "minio"


async def upload_local_file_to_storage(
    local_path: Path,
    storage_path: Optional[str] = None,
    delete_local: bool = False,
    category: StorageCategory = "outputs"
) -> Dict[str, Any]:
    """
    Upload a local file to the configured storage backend.

    Args:
        local_path: Path to the local file
        storage_path: Optional path in storage (defaults to filename)
        delete_local: Whether to delete local file after upload
        category: Storage category ("skills", "uploads", "outputs")

    Returns:
        Dict with file info: path, url, name, size, type, storage
    """
    from config import get_settings
    settings = get_settings()

    if not local_path.exists():
        raise FileNotFoundError(f"Local file not found: {local_path}")

    # Determine storage path
    if storage_path is None:
        storage_path = local_path.name

    # Get file info
    file_size = local_path.stat().st_size
    file_ext = local_path.suffix.lower()
    content_type, _ = mimetypes.guess_type(str(local_path))

    file_type_map = {
        '.json': 'json', '.xlsx': 'excel', '.xls': 'excel',
        '.csv': 'csv', '.pdf': 'pdf', '.html': 'html',
        '.png': 'image', '.jpg': 'image', '.jpeg': 'image',
        '.gif': 'image', '.svg': 'image', '.txt': 'text',
        '.md': 'markdown', '.docx': 'word', '.pptx': 'pptx'
    }
    file_type = file_type_map.get(file_ext, 'file')

    storage_type = settings.get_storage_type_for(category)

    if storage_type == "minio":
        # Upload to MinIO
        storage = get_storage_backend(category)

        # Read local file and upload
        content = local_path.read_bytes()
        await storage.write_file(storage_path, content, content_type)

        # Generate URL (通过 /storage/{category} 路由访问)
        url = f"/storage/{category}/{storage_path}"

        # Optionally delete local file
        if delete_local:
            local_path.unlink(missing_ok=True)

        return {
            "path": storage_path,
            "type": file_type,
            "name": local_path.name,
            "url": url,
            "size": file_size,
            "storage": "minio"
        }
    else:
        # Local storage - just return the path
        return {
            "path": str(local_path),
            "type": file_type,
            "name": local_path.name,
            "url": f"/{category}/{local_path.name}",
            "size": file_size,
            "storage": "local"
        }


def upload_local_file_to_storage_sync(
    local_path: Path,
    storage_path: Optional[str] = None,
    delete_local: bool = False,
    category: StorageCategory = "outputs"
) -> Dict[str, Any]:
    """Synchronous version of upload_local_file_to_storage.

    For local storage, returns file info directly without async.
    For MinIO storage, creates a new event loop (safe when not in async context).
    """
    from config import get_settings
    settings = get_settings()

    if not local_path.exists():
        raise FileNotFoundError(f"Local file not found: {local_path}")

    # Get file info
    file_size = local_path.stat().st_size
    file_ext = local_path.suffix.lower()
    content_type, _ = mimetypes.guess_type(str(local_path))

    file_type_map = {
        '.json': 'json', '.xlsx': 'excel', '.xls': 'excel',
        '.csv': 'csv', '.pdf': 'pdf', '.html': 'html',
        '.png': 'image', '.jpg': 'image', '.jpeg': 'image',
        '.gif': 'image', '.svg': 'image', '.txt': 'text',
        '.md': 'markdown', '.docx': 'word', '.pptx': 'pptx'
    }
    file_type = file_type_map.get(file_ext, 'file')

    storage_type = settings.get_storage_type_for(category)

    # For local storage, no async needed - return directly
    if storage_type != "minio":
        return {
            "path": str(local_path),
            "type": file_type,
            "name": local_path.name,
            "url": f"/{category}/{local_path.name}",
            "size": file_size,
            "storage": "local"
        }

    # For MinIO storage, need async
    try:
        # Try to get running loop (if we're in async context)
        loop = asyncio.get_running_loop()
        # We're in async context, can't use run_until_complete
        # Just return local info, the async caller should handle MinIO upload
        print(f"[Storage] 检测到已有事件循环，跳过 MinIO 上传，使用本地路径")
        return {
            "path": str(local_path),
            "type": file_type,
            "name": local_path.name,
            "url": f"/{category}/{local_path.name}",
            "size": file_size,
            "storage": "local"
        }
    except RuntimeError:
        # No running loop, safe to create one
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(
                upload_local_file_to_storage(local_path, storage_path, delete_local, category)
            )
        finally:
            loop.close()


async def sync_outputs_dir_to_storage(
    outputs_dir: Path,
    since_seconds: int = 30,
    delete_local: bool = False
) -> list:
    """
    Sync recently created files from local outputs dir to storage.
    Only syncs if outputs_storage_type is "minio".

    Args:
        outputs_dir: Local outputs directory
        since_seconds: Only sync files created within this many seconds
        delete_local: Whether to delete local files after upload

    Returns:
        List of uploaded file info dicts
    """
    if not is_minio_storage("outputs"):
        return []  # No sync needed for local storage

    uploaded = []
    cutoff_time = datetime.now().timestamp() - since_seconds

    extensions = ['.json', '.xlsx', '.xls', '.csv', '.pdf', '.html',
                  '.png', '.jpg', '.jpeg', '.gif', '.svg', '.txt',
                  '.md', '.docx', '.pptx']

    for ext in extensions:
        for f in outputs_dir.glob(f"*{ext}"):
            if f.stat().st_mtime > cutoff_time:
                try:
                    result = await upload_local_file_to_storage(
                        f, storage_path=f.name, delete_local=delete_local, category="outputs"
                    )
                    uploaded.append(result)
                except Exception as e:
                    print(f"[Storage] Failed to upload {f.name}: {e}")

    return uploaded


def ensure_storage_url(file_info: Dict[str, Any], category: StorageCategory = "outputs") -> Dict[str, Any]:
    """
    Ensure file_info has correct URL based on storage type.
    Uploads to MinIO if needed.
    """
    if not is_minio_storage(category):
        return file_info

    # If it's a local path, upload to MinIO
    local_path = Path(file_info.get("path", ""))
    if local_path.exists() and local_path.is_file():
        try:
            result = upload_local_file_to_storage_sync(local_path, category=category)
            file_info.update(result)
        except Exception as e:
            print(f"[Storage] Failed to sync file: {e}")

    return file_info


# ============ Skills 文件夹同步 ============

async def sync_skill_folder_to_minio(local_folder: Path, folder_name: str) -> int:
    """
    将本地 skill 文件夹同步到 MinIO（双写）

    Args:
        local_folder: 本地文件夹路径
        folder_name: MinIO 中的文件夹名（通常是 skill_id）

    Returns:
        上传的文件数量
    """
    if not is_minio_storage("skills"):
        return 0

    if not local_folder.exists():
        return 0

    storage = get_storage_backend("skills")
    uploaded_count = 0

    for file_path in local_folder.rglob("*"):
        if file_path.is_file():
            # 计算相对路径
            rel_path = file_path.relative_to(local_folder)
            minio_path = f"{folder_name}/{rel_path}"

            try:
                content = file_path.read_bytes()
                content_type, _ = mimetypes.guess_type(str(file_path))
                await storage.write_file(minio_path, content, content_type)
                uploaded_count += 1
            except Exception as e:
                print(f"[Skills Sync] 上传失败 {minio_path}: {e}")

    print(f"[Skills Sync] 同步完成: {folder_name}, 共 {uploaded_count} 个文件")
    return uploaded_count


def sync_skill_folder_to_minio_sync(local_folder: Path, folder_name: str) -> int:
    """同步版本的 sync_skill_folder_to_minio"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(
            sync_skill_folder_to_minio(local_folder, folder_name)
        )
    finally:
        loop.close()


async def delete_skill_folder_from_storage(folder_name: str, local_folder: Path = None):
    """
    从 MinIO 和本地删除 skill 文件夹（双删）

    Args:
        folder_name: MinIO 中的文件夹名（通常是 skill_id）
        local_folder: 本地文件夹路径（可选，如果提供则同时删除本地）
    """
    import shutil

    # 1. 删除本地
    if local_folder and local_folder.exists():
        try:
            shutil.rmtree(local_folder)
            print(f"[Skills Delete] 本地已删除: {local_folder}")
        except Exception as e:
            print(f"[Skills Delete] 本地删除失败: {e}")

    # 2. 删除 MinIO
    if is_minio_storage("skills"):
        storage = get_storage_backend("skills")
        try:
            # 使用 rmdir 删除整个文件夹（所有以 folder_name/ 开头的文件）
            await storage.rmdir(folder_name)
            print(f"[Skills Delete] MinIO 已删除: {folder_name}/")
        except Exception as e:
            print(f"[Skills Delete] MinIO 删除失败: {e}")
