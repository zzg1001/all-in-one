import uuid
import shutil
import zipfile
import tempfile
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func
from typing import List, Optional
from database import get_db
from config import get_uploads_dir
from models.data_note import DataNote
from schemas.data_note import DataNoteCreate, DataNoteUpdate, DataNoteResponse, FolderCreate, MoveToFolder

router = APIRouter(prefix="/api", tags=["Data Notes"])

MAX_FOLDER_LEVEL = 3  # 最大文件夹层级

# 使用统一配置的上传目录
UPLOADS_DIR = get_uploads_dir()


def get_user_id(x_user_id: Optional[str] = Header(None)) -> str:
    """获取用户ID

    当前：从请求头 X-User-ID 获取，由前端生成的匿名ID
    将来：从 JWT token 或 session 中获取真实用户ID
    """
    if x_user_id:
        return x_user_id
    return "anonymous"


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传文件"""
    # 生成唯一文件名
    ext = Path(file.filename).suffix if file.filename else ""
    unique_name = f"{uuid.uuid4()}{ext}"
    file_path = UPLOADS_DIR / unique_name

    # 保存文件
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "url": f"/uploads/{unique_name}",
        "name": file.filename,
        "size": file_path.stat().st_size
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
    """获取当前用户的数据便签

    Args:
        q: 搜索关键词（搜索名称和描述）
        favorited_only: 只返回收藏的便签
        parent_id: 父文件夹ID，不传则获取根目录，传 'all' 获取全部
        agent_id: Agent ID，只返回该 Agent 关联的便签
    """
    query = db.query(DataNote).filter(DataNote.user_id == user_id)

    # 按 Agent 过滤
    if agent_id:
        query = query.filter(DataNote.agent_id == agent_id)

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
                DataNote.user_id == user_id,
                DataNote.parent_id == note.id
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
    """删除数据便签（如果是文件夹则递归删除内容）"""
    note = db.query(DataNote).filter(
        DataNote.id == note_id,
        DataNote.user_id == user_id
    ).first()

    if not note:
        raise HTTPException(status_code=404, detail="数据便签不存在")

    # 如果是文件夹，递归删除内容
    if note.file_type == 'folder':
        delete_folder_contents(db, user_id, note_id)

    db.delete(note)
    db.commit()

    return None


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
        add_folder_to_zip(db, user_id, note_id, zf, "", UPLOADS_DIR)

    return FileResponse(
        path=zip_path,
        filename=f"{note.name}.zip",
        media_type="application/zip"
    )


def add_folder_to_zip(db: Session, user_id: str, folder_id: str, zf: zipfile.ZipFile, path_prefix: str, uploads_dir: Path):
    """递归添加文件夹内容到zip"""
    children = db.query(DataNote).filter(
        DataNote.user_id == user_id,
        DataNote.parent_id == folder_id
    ).all()

    for child in children:
        if child.file_type == 'folder':
            # 递归处理子文件夹
            new_prefix = f"{path_prefix}{child.name}/" if path_prefix else f"{child.name}/"
            add_folder_to_zip(db, user_id, child.id, zf, new_prefix, uploads_dir)
        elif child.file_url:
            # 添加文件
            file_name = child.file_url.split('/')[-1]
            file_path = uploads_dir / file_name
            if file_path.exists():
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
