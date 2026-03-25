import uuid
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional
from database import get_db
from models.favorite import UserFavorite
from schemas.favorite import FavoriteCreate, FavoriteDelete, FavoriteResponse, FavoriteListResponse

router = APIRouter(prefix="/api/favorites", tags=["Favorites"])


def get_user_id(x_user_id: Optional[str] = Header(None)) -> str:
    """获取用户ID

    当前：从请求头 X-User-ID 获取，由前端生成的匿名ID
    将来：从 JWT token 或 session 中获取真实用户ID
    """
    if x_user_id:
        return x_user_id
    # 没有提供时返回默认用户（便于测试）
    return "anonymous"


@router.get("", response_model=FavoriteListResponse)
async def get_favorites(
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """获取当前用户的所有收藏"""
    favorites = db.query(UserFavorite).filter(
        UserFavorite.user_id == user_id
    ).all()

    skills = [f.item_id for f in favorites if f.item_type == "skill"]
    workflows = [f.item_id for f in favorites if f.item_type == "workflow"]

    return FavoriteListResponse(skills=skills, workflows=workflows)


@router.post("", response_model=FavoriteResponse)
async def add_favorite(
    data: FavoriteCreate,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """添加收藏"""
    favorite = UserFavorite(
        id=str(uuid.uuid4()),
        user_id=user_id,
        item_type=data.item_type,
        item_id=data.item_id
    )

    try:
        db.add(favorite)
        db.commit()
        db.refresh(favorite)
        return favorite
    except IntegrityError:
        db.rollback()
        # 已经收藏过了，返回现有的
        existing = db.query(UserFavorite).filter(
            UserFavorite.user_id == user_id,
            UserFavorite.item_type == data.item_type,
            UserFavorite.item_id == data.item_id
        ).first()
        if existing:
            return existing
        raise HTTPException(status_code=400, detail="添加收藏失败")


@router.delete("")
async def remove_favorite(
    data: FavoriteDelete,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """取消收藏"""
    result = db.query(UserFavorite).filter(
        UserFavorite.user_id == user_id,
        UserFavorite.item_type == data.item_type,
        UserFavorite.item_id == data.item_id
    ).delete()

    db.commit()

    if result == 0:
        raise HTTPException(status_code=404, detail="收藏不存在")

    return {"message": "已取消收藏"}


@router.post("/toggle")
async def toggle_favorite(
    data: FavoriteCreate,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """切换收藏状态（收藏/取消收藏）"""
    existing = db.query(UserFavorite).filter(
        UserFavorite.user_id == user_id,
        UserFavorite.item_type == data.item_type,
        UserFavorite.item_id == data.item_id
    ).first()

    if existing:
        # 已收藏，取消收藏
        db.delete(existing)
        db.commit()
        return {"favorited": False, "item_id": data.item_id}
    else:
        # 未收藏，添加收藏
        favorite = UserFavorite(
            id=str(uuid.uuid4()),
            user_id=user_id,
            item_type=data.item_type,
            item_id=data.item_id
        )
        db.add(favorite)
        db.commit()
        return {"favorited": True, "item_id": data.item_id}
