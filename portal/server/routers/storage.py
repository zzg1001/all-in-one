"""
Storage API routes.
Provides file access for both local and MinIO storage backends.
Supports category-based storage configuration.
"""
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse
from pathlib import Path
import mimetypes

from config import get_settings, get_outputs_dir, get_uploads_dir, get_file_manage_dir, get_skills_storage_dir
from services.storage.utils import get_storage_backend, is_minio_storage

router = APIRouter(prefix="/storage", tags=["storage"])


async def get_file_from_storage(file_path: str, category: str):
    """
    Get a file from storage.
    优先读本地，本地没有再从 MinIO 拉取（并缓存到本地）。

    Args:
        file_path: Relative path to the file
        category: "outputs", "uploads", "file_manage", or "skills"

    Returns:
        tuple: (content, content_type, filename) or raises HTTPException
    """
    settings = get_settings()

    # Guess content type
    content_type, _ = mimetypes.guess_type(file_path)
    if not content_type:
        content_type = "application/octet-stream"

    # Get local directory
    dir_map = {
        "outputs": get_outputs_dir(),
        "uploads": get_uploads_dir(),
        "file_manage": get_file_manage_dir(),  # File Manage 独立目录
        "skills": get_skills_storage_dir(),
    }
    local_dir = dir_map.get(category, get_outputs_dir())
    local_path = local_dir / file_path

    # 1. 优先读本地
    if local_path.exists():
        return None, content_type, local_path  # None content = 用 FileResponse

    # 2. 本地没有，从 MinIO 拉取
    if is_minio_storage(category):
        storage = get_storage_backend(category)
        try:
            content = await storage.read_file(file_path)

            # 3. 缓存到本地（下次直接读本地）
            try:
                local_path.parent.mkdir(parents=True, exist_ok=True)
                local_path.write_bytes(content)
                print(f"[Storage] 从 MinIO 拉取并缓存: {category}/{file_path}")
            except Exception as e:
                print(f"[Storage] 缓存到本地失败: {e}")

            return content, content_type, Path(file_path).name
        except Exception as e:
            print(f"[Storage] MinIO 读取失败 ({category}/{file_path}): {e}")

    raise HTTPException(status_code=404, detail=f"文件不存在: {file_path}")


@router.get("/outputs/{file_path:path}")
async def get_output_file(file_path: str):
    """
    Get a file from outputs storage.
    Uses local storage by default (configurable via OUTPUTS_STORAGE_TYPE).
    """
    content, content_type, path_or_name = await get_file_from_storage(file_path, "outputs")

    if content is None:
        # Local file
        return FileResponse(
            path=path_or_name,
            media_type=content_type,
            filename=path_or_name.name
        )

    # MinIO content
    if file_path.lower().endswith('.pdf'):
        return Response(
            content=content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="{path_or_name}"',
                "Content-Type": "application/pdf"
            }
        )

    return Response(
        content=content,
        media_type=content_type,
        headers={
            "Content-Disposition": f'inline; filename="{path_or_name}"'
        }
    )


@router.get("/uploads/{file_path:path}")
async def get_upload_file(file_path: str):
    """
    Get a file from uploads storage (输入框临时上传).
    Uses local storage by default.
    """
    content, content_type, path_or_name = await get_file_from_storage(file_path, "uploads")

    if content is None:
        # Local file
        return FileResponse(
            path=path_or_name,
            media_type=content_type,
            filename=path_or_name.name
        )

    # MinIO content
    return Response(
        content=content,
        media_type=content_type,
        headers={
            "Content-Disposition": f'inline; filename="{path_or_name}"'
        }
    )


@router.get("/file-manage/{file_path:path}")
async def get_file_manage_file(file_path: str):
    """
    Get a file from File Manage storage (数据便签).
    Uses MinIO by default for multi-node sharing.
    """
    content, content_type, path_or_name = await get_file_from_storage(file_path, "file_manage")

    if content is None:
        # Local file
        return FileResponse(
            path=path_or_name,
            media_type=content_type,
            filename=path_or_name.name
        )

    # MinIO content
    return Response(
        content=content,
        media_type=content_type,
        headers={
            "Content-Disposition": f'inline; filename="{path_or_name}"'
        }
    )


@router.get("/skills/{file_path:path}")
async def get_skill_file(file_path: str):
    """
    Get a file from skills storage.
    Uses MinIO by default (configurable via SKILLS_STORAGE_TYPE).
    """
    content, content_type, path_or_name = await get_file_from_storage(file_path, "skills")

    if content is None:
        # Local file
        return FileResponse(
            path=path_or_name,
            media_type=content_type,
            filename=path_or_name.name
        )

    # MinIO content
    return Response(
        content=content,
        media_type=content_type,
        headers={
            "Content-Disposition": f'inline; filename="{path_or_name}"'
        }
    )


@router.get("/outputs/{file_path:path}/url")
async def get_output_file_url(file_path: str, expires_in: int = 3600):
    """
    Get a presigned URL for a file (MinIO only).
    For local storage, returns the direct API path.
    """
    if is_minio_storage("outputs"):
        storage = get_storage_backend("outputs")
        try:
            if not await storage.exists(file_path):
                raise HTTPException(status_code=404, detail=f"文件不存在: {file_path}")

            url = await storage.get_presigned_url(file_path, expires_in=expires_in)
            return {"url": url, "expires_in": expires_in}
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"文件不存在: {file_path}")
    else:
        # Local storage - return API path
        outputs_dir = get_outputs_dir()
        local_path = outputs_dir / file_path

        if not local_path.exists():
            raise HTTPException(status_code=404, detail=f"文件不存在: {file_path}")

        return {"url": f"/api/storage/outputs/{file_path}", "expires_in": None}


@router.get("/skills/{file_path:path}/url")
async def get_skill_file_url(file_path: str, expires_in: int = 3600):
    """
    Get a presigned URL for a skill file (MinIO only).
    For local storage, returns the direct API path.
    """
    if is_minio_storage("skills"):
        storage = get_storage_backend("skills")
        try:
            if not await storage.exists(file_path):
                raise HTTPException(status_code=404, detail=f"文件不存在: {file_path}")

            url = await storage.get_presigned_url(file_path, expires_in=expires_in)
            return {"url": url, "expires_in": expires_in}
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"文件不存在: {file_path}")
    else:
        # Local storage - return API path
        skills_dir = get_skills_storage_dir()
        local_path = skills_dir / file_path

        if not local_path.exists():
            raise HTTPException(status_code=404, detail=f"文件不存在: {file_path}")

        return {"url": f"/api/storage/skills/{file_path}", "expires_in": None}
