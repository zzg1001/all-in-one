import uuid
import shutil
import zipfile
import tempfile
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func
from typing import List, Optional, Tuple
from app.core.database import get_db
from app.core.config import get_uploads_dir, get_file_manage_dir, get_outputs_dir
from portal.models.data_note import DataNote
from portal.schemas.data_note import DataNoteCreate, DataNoteUpdate, DataNoteResponse, FolderCreate, MoveToFolder


async def ensure_local_file(file_url: str) -> Optional[Path]:
    """
    确保文件存在于本地。（异步版本）

    Args:
        file_url: 文件 URL，如 /file-manage/xxx/yyy.pdf

    Returns:
        本地文件路径，如果文件不存在则返回 None
    """
    # 解析路径
    if file_url.startswith('/file-manage/'):
        relative_path = file_url[len('/file-manage/'):]
        local_dir = get_file_manage_dir()
    elif file_url.startswith('/uploads/'):
        relative_path = file_url[len('/uploads/'):]
        local_dir = get_uploads_dir()
    elif file_url.startswith('/outputs/'):
        relative_path = file_url[len('/outputs/'):]
        local_dir = get_outputs_dir()
    else:
        return None

    local_path = local_dir / relative_path

    # 本地存在，直接返回
    if local_path.exists():
        return local_path

    return None


def ensure_local_file_sync(file_url: str) -> Optional[Path]:
    """
    确保文件存在于本地。（同步版本）
    """
    # 解析路径
    if file_url.startswith('/file-manage/'):
        relative_path = file_url[len('/file-manage/'):]
        local_dir = get_file_manage_dir()
    elif file_url.startswith('/uploads/'):
        relative_path = file_url[len('/uploads/'):]
        local_dir = get_uploads_dir()
    elif file_url.startswith('/outputs/'):
        relative_path = file_url[len('/outputs/'):]
        local_dir = get_outputs_dir()
    else:
        return None

    local_path = local_dir / relative_path

    # 本地存在，直接返回
    if local_path.exists():
        return local_path

    return None

# 向量服务（可选，导入失败不影响基础功能）
# 使用延迟导入避免循环依赖
_vector_service_available = False
_vector_service = None

def get_vector_service():
    """延迟获取向量服务，避免循环导入"""
    global _vector_service_available, _vector_service

    # 检查是否启用向量数据库
    from app.core.config import get_settings
    settings = get_settings()
    if not settings.vector_db_enabled:
        return None

    if _vector_service is not None:
        return _vector_service
    try:
        # 直接导入模块，不触发 services/__init__.py
        import importlib.util
        import os
        module_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'services', 'vector_service.py')
        spec = importlib.util.spec_from_file_location('vector_service', module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _vector_service = module.get_vector_service()
        _vector_service_available = True
        print(f"[DataNotes] Vector service loaded successfully")
        return _vector_service
    except Exception as e:
        print(f"[DataNotes] Vector service not available: {e}")
        import traceback
        traceback.print_exc()
        return None

router = APIRouter(prefix="/api", tags=["Data Notes"])

MAX_FOLDER_LEVEL = 3  # 最大文件夹层级

# 使用统一配置的目录
UPLOADS_DIR = get_uploads_dir()
FILE_MANAGE_DIR = get_file_manage_dir()  # File Manage 独立目录


def get_accessible_agent_ids(db: Session, agent_id: str) -> Tuple[List[str], bool]:
    """
    获取 Agent 可访问的所有 agent_id 列表

    Args:
        db: 数据库会话
        agent_id: 当前 Agent ID

    Returns:
        (agent_ids, access_all): agent_ids 是可访问的ID列表，access_all 表示是否可访问所有数据
    """
    from portal.models.agent import Agent

    if not agent_id:
        return [], False

    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        return [agent_id], False  # Agent不存在，只能访问自己的

    # 自己的数据始终可访问
    accessible = [agent_id]

    # 检查额外权限
    extra_ids = agent.accessible_agent_ids or []

    # 特殊值 "*" 表示可访问所有
    if "*" in extra_ids:
        return [], True  # access_all = True

    # 添加额外授权的 agent_ids
    for aid in extra_ids:
        if aid and aid not in accessible:
            accessible.append(aid)

    return accessible, False


def get_user_id(x_user_id: Optional[str] = Header(None)) -> str:
    """获取用户ID

    当前：从请求头 X-User-ID 获取，由前端生成的匿名ID
    将来：从 JWT token 或 session 中获取真实用户ID
    """
    if x_user_id:
        return x_user_id
    return "anonymous"


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    agent_id: Optional[str] = None
):
    """File Manage 上传文件（按 agent_id 隔离存储，本地存储模式）

    Args:
        file: 上传的文件
        agent_id: Agent ID，文件将存储在 {agent_id}/ 目录下

    Note:
        File Manage 使用本地存储，文件保存在 file_manage 目录下
    """
    # 生成唯一文件名
    ext = Path(file.filename).suffix if file.filename else ""
    unique_name = f"{uuid.uuid4()}{ext}"

    # 按 agent_id 隔离存储路径
    if agent_id:
        relative_path = f"{agent_id}/{unique_name}"
        agent_dir = FILE_MANAGE_DIR / agent_id
        agent_dir.mkdir(parents=True, exist_ok=True)
        local_path = agent_dir / unique_name
    else:
        relative_path = unique_name
        local_path = FILE_MANAGE_DIR / unique_name

    # 读取文件内容
    content = await file.read()
    file_size = len(content)

    # 写入本地存储
    try:
        with open(local_path, "wb") as buffer:
            buffer.write(content)
        print(f"[FileManage] 本地写入成功: {local_path}")
    except Exception as e:
        print(f"[FileManage] 本地写入失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {e}")

    return {
        "url": f"/file-manage/{relative_path}",
        "name": file.filename,
        "size": file_size,
        "agent_id": agent_id
    }


@router.get("/data-notes", response_model=List[DataNoteResponse])
async def get_data_notes(
    q: Optional[str] = None,
    favorited_only: bool = False,
    parent_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """获取数据便签（基于 Agent 权限）

    数据权限规则：
    - Agent 自己的数据始终可访问
    - 如果 Agent 配置了 accessible_agent_ids，还可访问其他 Agent 的数据
    - 如果 accessible_agent_ids 包含 "*"，可访问所有数据

    Args:
        q: 搜索关键词（搜索名称和描述）
        favorited_only: 只返回收藏的便签
        parent_id: 父文件夹ID，不传则获取根目录，传 'all' 获取全部
        agent_id: 当前 Agent ID（用于确定数据权限）
    """
    query = db.query(DataNote).filter(
        DataNote.deleted_at.is_(None)  # 排除软删除的记录
    )

    # 基于 Agent 权限过滤数据
    if agent_id:
        accessible_ids, access_all = get_accessible_agent_ids(db, agent_id)
        if not access_all:
            # 只能访问指定的 agent 数据
            query = query.filter(DataNote.agent_id.in_(accessible_ids))
        # access_all = True 时不过滤，可访问所有数据
    else:
        # 没有 agent_id 时，返回空（或者可以返回所有无 agent_id 的数据）
        query = query.filter(DataNote.agent_id.is_(None))

    if favorited_only:
        query = query.filter(DataNote.is_favorited == True)

    # 按文件夹过滤
    if parent_id != 'all':
        if parent_id:
            query = query.filter(DataNote.parent_id == parent_id)
        else:
            query = query.filter(DataNote.parent_id.is_(None))

    if q and q.strip():
        search_term = f"%{q.strip()}%"
        query = query.filter(
            (DataNote.name.ilike(search_term)) |
            (DataNote.description.ilike(search_term))
        )

    # 文件夹排在前面
    notes = query.order_by(
        (DataNote.file_type == 'folder').desc(),
        DataNote.created_at.desc()
    ).all()

    # 计算文件夹内的项目数
    result = []
    for note in notes:
        note_dict = {
            "id": note.id,
            "user_id": note.user_id,
            "agent_id": note.agent_id,
            "name": note.name,
            "description": note.description,
            "file_type": note.file_type,
            "file_url": note.file_url,
            "file_size": note.file_size,
            "source_skill": note.source_skill,
            "is_favorited": note.is_favorited,
            "parent_id": note.parent_id,
            "level": note.level,
            "created_at": note.created_at,
            "updated_at": note.updated_at,
            "item_count": None
        }
        if note.file_type == 'folder':
            count = db.query(sql_func.count(DataNote.id)).filter(
                DataNote.parent_id == note.id,
                DataNote.deleted_at.is_(None)
            ).scalar()
            note_dict["item_count"] = count
        result.append(DataNoteResponse(**note_dict))

    return result


@router.get("/data-notes/{note_id}", response_model=DataNoteResponse)
async def get_data_note(
    note_id: str,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """获取单个数据便签"""
    note = db.query(DataNote).filter(
        DataNote.id == note_id,
        DataNote.user_id == user_id
    ).first()

    if not note:
        raise HTTPException(status_code=404, detail="数据便签不存在")

    return note


@router.post("/data-notes", response_model=DataNoteResponse, status_code=201)
async def create_data_note(
    data: DataNoteCreate,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """创建数据便签"""
    level = 0
    if data.parent_id:
        # 检查父文件夹
        parent = db.query(DataNote).filter(
            DataNote.id == data.parent_id,
            DataNote.user_id == user_id,
            DataNote.file_type == 'folder'
        ).first()
        if not parent:
            raise HTTPException(status_code=404, detail="父文件夹不存在")
        level = parent.level + 1

    note = DataNote(
        id=str(uuid.uuid4()),
        user_id=user_id,
        agent_id=data.agent_id,
        name=data.name,
        description=data.description,
        file_type=data.file_type,
        file_url=data.file_url,
        file_size=data.file_size,
        source_skill=data.source_skill,
        is_favorited=False,
        parent_id=data.parent_id,
        level=level
    )

    db.add(note)
    db.commit()
    db.refresh(note)

    # 如果是文件（非文件夹），索引到向量数据库（可选功能）
    if note.file_type != 'folder' and note.file_url:
        print(f"[DataNotes] Starting vector indexing for file: {note.id}, agent_id: {note.agent_id}")
        try:
            vector_service = get_vector_service()
            if vector_service:
                # 确保文件存在于本地（从 MinIO 拉取如果需要）
                local_path = await ensure_local_file(note.file_url)
                if local_path:
                    print(f"[DataNotes] Indexing file path: {local_path}")
                    chunk_count = await vector_service.index_file(
                        file_id=note.id,
                        file_path=str(local_path),
                        user_id=user_id,
                        agent_id=note.agent_id,
                        metadata={"name": note.name, "file_type": note.file_type}
                    )
                    print(f"[DataNotes] Vector indexing completed: {chunk_count} chunks indexed")
                else:
                    print(f"[DataNotes] 无法获取文件: {note.file_url}")
            else:
                print("[DataNotes] Vector service is None")
        except Exception as e:
            import traceback
            print(f"[DataNotes] Vector indexing failed: {e}")
            traceback.print_exc()
            # 不阻塞主流程

    return note


@router.put("/data-notes/{note_id}", response_model=DataNoteResponse)
async def update_data_note(
    note_id: str,
    data: DataNoteUpdate,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """更新数据便签"""
    note = db.query(DataNote).filter(
        DataNote.id == note_id,
        DataNote.user_id == user_id
    ).first()

    if not note:
        raise HTTPException(status_code=404, detail="数据便签不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(note, key, value)

    db.commit()
    db.refresh(note)
    return note


@router.delete("/data-notes/{note_id}", status_code=204)
async def delete_data_note(
    note_id: str,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """软删除数据便签（标记 deleted_at，物理文件由清理任务异步删除）"""
    from datetime import datetime

    note = db.query(DataNote).filter(
        DataNote.id == note_id,
        DataNote.user_id == user_id,
        DataNote.deleted_at.is_(None)  # 只能删除未删除的
    ).first()

    if not note:
        raise HTTPException(status_code=404, detail="数据便签不存在")

    now = datetime.now()

    # 如果是文件夹，递归软删除内容
    if note.file_type == 'folder':
        soft_delete_folder_contents(db, user_id, note_id, now)

    # 软删除当前记录
    note.deleted_at = now
    db.commit()

    print(f"[DataNotes] 软删除: {note.name} (id={note_id})")
    return None


def soft_delete_folder_contents(db: Session, user_id: str, folder_id: str, deleted_at):
    """递归软删除文件夹内容"""
    children = db.query(DataNote).filter(
        DataNote.user_id == user_id,
        DataNote.parent_id == folder_id,
        DataNote.deleted_at.is_(None)
    ).all()

    for child in children:
        if child.file_type == 'folder':
            soft_delete_folder_contents(db, user_id, child.id, deleted_at)
        child.deleted_at = deleted_at


async def delete_physical_file(file_url: str):
    """删除物理文件（本地存储）"""
    from app.core.config import get_outputs_dir

    if not file_url:
        return

    # 解析相对路径
    if file_url.startswith('/file-manage/'):
        relative_path = file_url[len('/file-manage/'):]
        local_path = FILE_MANAGE_DIR / relative_path  # 使用独立的 file_manage 目录
    elif file_url.startswith('/uploads/'):
        relative_path = file_url[len('/uploads/'):]
        local_path = UPLOADS_DIR / relative_path
    elif file_url.startswith('/outputs/'):
        relative_path = file_url[len('/outputs/'):]
        local_path = get_outputs_dir() / relative_path
    else:
        return

    # 删除本地文件
    try:
        if local_path.exists():
            local_path.unlink()
            print(f"[Delete] 本地文件已删除: {local_path}")
    except Exception as e:
        print(f"[Delete] 本地文件删除失败: {e}")


def collect_files_in_folder(db: Session, user_id: str, folder_id: str) -> List[tuple]:
    """收集文件夹内所有文件的信息（用于删除文件和向量索引）

    Returns:
        List of (file_id, file_url) tuples
    """
    files = []
    children = db.query(DataNote).filter(
        DataNote.user_id == user_id,
        DataNote.parent_id == folder_id
    ).all()

    for child in children:
        if child.file_type == 'folder':
            files.extend(collect_files_in_folder(db, user_id, child.id))
        elif child.file_url:
            files.append((child.id, child.file_url))

    return files


def delete_folder_contents(db: Session, user_id: str, folder_id: str):
    """递归删除文件夹内容"""
    children = db.query(DataNote).filter(
        DataNote.user_id == user_id,
        DataNote.parent_id == folder_id
    ).all()

    for child in children:
        if child.file_type == 'folder':
            delete_folder_contents(db, user_id, child.id)
        db.delete(child)


@router.post("/data-notes/{note_id}/toggle-favorite")
async def toggle_favorite(
    note_id: str,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """切换便签的收藏状态"""
    note = db.query(DataNote).filter(
        DataNote.id == note_id,
        DataNote.user_id == user_id
    ).first()

    if not note:
        raise HTTPException(status_code=404, detail="数据便签不存在")

    note.is_favorited = not note.is_favorited
    db.commit()
    db.refresh(note)

    return {"id": note.id, "is_favorited": note.is_favorited}


@router.post("/data-notes/folder", response_model=DataNoteResponse, status_code=201)
async def create_folder(
    data: FolderCreate,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """创建文件夹并移入选中的文件"""
    level = 0
    if data.parent_id:
        parent = db.query(DataNote).filter(
            DataNote.id == data.parent_id,
            DataNote.user_id == user_id,
            DataNote.file_type == 'folder'
        ).first()
        if not parent:
            raise HTTPException(status_code=404, detail="父文件夹不存在")
        level = parent.level + 1

    if level >= MAX_FOLDER_LEVEL:
        raise HTTPException(status_code=400, detail=f"最多支持 {MAX_FOLDER_LEVEL} 层文件夹")

    # 检查是否已存在同名文件夹（防止重复创建）
    existing_query = db.query(DataNote).filter(
        DataNote.user_id == user_id,
        DataNote.name == data.name,
        DataNote.file_type == 'folder'
    )
    if data.parent_id:
        existing_query = existing_query.filter(DataNote.parent_id == data.parent_id)
    else:
        existing_query = existing_query.filter(DataNote.parent_id.is_(None))
    existing = existing_query.first()

    if existing:
        # 已存在，直接返回
        item_count = db.query(sql_func.count(DataNote.id)).filter(
            DataNote.user_id == user_id,
            DataNote.parent_id == existing.id
        ).scalar()
        return DataNoteResponse(
            id=existing.id,
            user_id=existing.user_id,
            name=existing.name,
            description=existing.description,
            file_type=existing.file_type,
            file_url=existing.file_url,
            file_size=existing.file_size,
            source_skill=existing.source_skill,
            is_favorited=existing.is_favorited,
            parent_id=existing.parent_id,
            level=existing.level,
            item_count=item_count,
            created_at=existing.created_at,
            updated_at=existing.updated_at
        )

    # 创建文件夹
    folder = DataNote(
        id=str(uuid.uuid4()),
        user_id=user_id,
        agent_id=data.agent_id,
        name=data.name,
        file_type='folder',
        file_url=None,
        is_favorited=False,
        parent_id=data.parent_id,
        level=level
    )
    db.add(folder)

    # 移动选中的文件到文件夹
    if data.item_ids:
        items = db.query(DataNote).filter(
            DataNote.id.in_(data.item_ids),
            DataNote.user_id == user_id
        ).all()
        for item in items:
            item.parent_id = folder.id
            item.level = level + 1

    db.commit()
    db.refresh(folder)

    # 计算项目数
    item_count = len(data.item_ids)
    return DataNoteResponse(
        id=folder.id,
        user_id=folder.user_id,
        name=folder.name,
        description=folder.description,
        file_type=folder.file_type,
        file_url=folder.file_url,
        file_size=folder.file_size,
        source_skill=folder.source_skill,
        is_favorited=folder.is_favorited,
        parent_id=folder.parent_id,
        level=folder.level,
        item_count=item_count,
        created_at=folder.created_at,
        updated_at=folder.updated_at
    )


@router.post("/data-notes/{note_id}/move", response_model=DataNoteResponse)
async def move_to_folder(
    note_id: str,
    data: MoveToFolder,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """移动文件到指定文件夹"""
    note = db.query(DataNote).filter(
        DataNote.id == note_id,
        DataNote.user_id == user_id
    ).first()

    if not note:
        raise HTTPException(status_code=404, detail="文件不存在")

    new_level = 0
    if data.target_folder_id:
        target = db.query(DataNote).filter(
            DataNote.id == data.target_folder_id,
            DataNote.user_id == user_id,
            DataNote.file_type == 'folder'
        ).first()
        if not target:
            raise HTTPException(status_code=404, detail="目标文件夹不存在")
        new_level = target.level + 1

        # 检查层级限制
        if note.file_type == 'folder':
            # 如果移动的是文件夹，检查其子项的最大深度
            max_child_depth = get_max_depth(db, user_id, note.id)
            if new_level + max_child_depth > MAX_FOLDER_LEVEL:
                raise HTTPException(status_code=400, detail=f"超出最大层级限制（{MAX_FOLDER_LEVEL}层）")

    note.parent_id = data.target_folder_id
    note.level = new_level

    # 如果是文件夹，更新所有子项的层级
    if note.file_type == 'folder':
        update_children_level(db, user_id, note.id, new_level + 1)

    db.commit()
    db.refresh(note)
    return note


def get_max_depth(db: Session, user_id: str, folder_id: str) -> int:
    """获取文件夹内最大深度"""
    children = db.query(DataNote).filter(
        DataNote.user_id == user_id,
        DataNote.parent_id == folder_id
    ).all()

    if not children:
        return 0

    max_depth = 0
    for child in children:
        if child.file_type == 'folder':
            depth = 1 + get_max_depth(db, user_id, child.id)
            max_depth = max(max_depth, depth)
        else:
            max_depth = max(max_depth, 0)
    return max_depth


def update_children_level(db: Session, user_id: str, folder_id: str, new_level: int):
    """递归更新子项层级"""
    children = db.query(DataNote).filter(
        DataNote.user_id == user_id,
        DataNote.parent_id == folder_id
    ).all()

    for child in children:
        child.level = new_level
        if child.file_type == 'folder':
            update_children_level(db, user_id, child.id, new_level + 1)


@router.get("/data-notes/{note_id}/download-zip")
async def download_folder_as_zip(
    note_id: str,
    x_user_id: Optional[str] = None,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    # 支持 query param 方式传递 user_id（用于下载链接）
    if x_user_id:
        user_id = x_user_id
    """下载文件夹为zip"""
    note = db.query(DataNote).filter(
        DataNote.id == note_id,
        DataNote.user_id == user_id
    ).first()

    if not note:
        raise HTTPException(status_code=404, detail="文件夹不存在")

    if note.file_type != 'folder':
        raise HTTPException(status_code=400, detail="只能下载文件夹")

    # 创建临时zip文件
    temp_dir = tempfile.mkdtemp()
    zip_path = Path(temp_dir) / f"{note.name}.zip"

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        add_folder_to_zip(db, user_id, note_id, zf, "")

    return FileResponse(
        path=zip_path,
        filename=f"{note.name}.zip",
        media_type="application/zip"
    )


def add_folder_to_zip(db: Session, user_id: str, folder_id: str, zf: zipfile.ZipFile, path_prefix: str):
    """递归添加文件夹内容到zip"""
    from app.core.config import get_outputs_dir

    children = db.query(DataNote).filter(
        DataNote.user_id == user_id,
        DataNote.parent_id == folder_id
    ).all()

    for child in children:
        if child.file_type == 'folder':
            # 递归处理子文件夹
            new_prefix = f"{path_prefix}{child.name}/" if path_prefix else f"{child.name}/"
            add_folder_to_zip(db, user_id, child.id, zf, new_prefix)
        elif child.file_url:
            # 确保文件存在于本地（从 MinIO 拉取如果需要）
            file_path = ensure_local_file_sync(child.file_url)
            if file_path and file_path.exists():
                arcname = f"{path_prefix}{child.name}" if path_prefix else child.name
                zf.write(file_path, arcname)


@router.get("/data-notes/{note_id}/files")
async def get_folder_files(
    note_id: str,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """获取文件夹内的文件（只取第一层，不递归子文件夹）"""
    note = db.query(DataNote).filter(
        DataNote.id == note_id,
        DataNote.user_id == user_id
    ).first()

    if not note:
        raise HTTPException(status_code=404, detail="文件夹不存在")

    if note.file_type != 'folder':
        raise HTTPException(status_code=400, detail="不是文件夹")

    # 只获取直接子文件（不包括子文件夹）
    children = db.query(DataNote).filter(
        DataNote.user_id == user_id,
        DataNote.parent_id == note_id,
        DataNote.file_type != 'folder'
    ).all()

    files = []
    for child in children:
        if child.file_url:
            files.append({
                "id": child.id,
                "name": child.name,
                "file_type": child.file_type,
                "file_url": child.file_url,
                "file_size": child.file_size
            })
    return files


def collect_folder_files_recursive(db: Session, user_id: str, folder_id: str, files: list):
    """递归收集文件夹内的所有文件（用于 zip 下载等场景）"""
    children = db.query(DataNote).filter(
        DataNote.user_id == user_id,
        DataNote.parent_id == folder_id
    ).all()

    for child in children:
        if child.file_type == 'folder':
            collect_folder_files_recursive(db, user_id, child.id, files)
        elif child.file_url:
            files.append({
                "id": child.id,
                "name": child.name,
                "file_type": child.file_type,
                "file_url": child.file_url,
                "file_size": child.file_size
            })


# ============ 向量搜索 API ============

from pydantic import BaseModel

class VectorSearchRequest(BaseModel):
    query: str
    agent_id: Optional[str] = None
    top_k: int = 5


class VectorSearchResult(BaseModel):
    id: str
    file_id: str
    content: str
    similarity: float
    metadata: dict = {}


@router.post("/data-notes/search", response_model=List[VectorSearchResult])
async def vector_search(
    request: VectorSearchRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """
    向量相似度搜索（基于 Agent 权限）

    从 Agent 可访问的文件中搜索与查询相关的内容片段。
    """
    try:
        vector_service = get_vector_service()
        if not vector_service:
            raise HTTPException(status_code=503, detail="向量搜索服务未初始化")

        # 获取可访问的 agent_ids
        accessible_ids, access_all = get_accessible_agent_ids(db, request.agent_id)

        results = await vector_service.search(
            query=request.query,
            agent_id=request.agent_id,
            agent_ids=accessible_ids if not access_all else None,  # None 表示不过滤
            access_all=access_all,
            top_k=request.top_k
        )
        return results
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.get("/data-notes/vector-stats")
async def get_vector_stats(
    agent_id: Optional[str] = None,
    user_id: str = Depends(get_user_id)
):
    """获取向量库统计信息"""
    try:
        vector_service = get_vector_service()
        if not vector_service:
            return {"file_count": 0, "chunk_count": 0, "status": "not_initialized"}
        stats = await vector_service.get_file_stats(agent_id=agent_id)
        stats["status"] = "ok"
        return stats
    except Exception as e:
        return {"file_count": 0, "chunk_count": 0, "status": f"error: {str(e)}"}
