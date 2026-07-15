from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models import Location, Post
from app.schemas.post import PostCreate, PostUpdate


def list_posts(db: Session, search: str | None, search_field: str, category: str | None, location_id: int | None, sort: str, page: int, size: int):
    filters = []
    if search:
        pattern = f"%{search}%"
        search_columns = {
            "title": (Post.title,),
            "content": (Post.content,),
            "nickname": (Post.nickname,),
            "all": (Post.title, Post.content, Post.nickname),
        }
        filters.append(or_(*(column.ilike(pattern) for column in search_columns[search_field])))
    if category:
        filters.append(Post.category == category)
    if location_id:
        filters.append(Post.location_id == location_id)
    order = (Post.views.desc(), Post.created_at.desc(), Post.id.desc()) if sort == "views" else (Post.created_at.desc(), Post.id.desc())
    total = db.scalar(select(func.count(Post.id)).where(*filters)) or 0
    items = db.scalars(select(Post).options(joinedload(Post.location)).where(*filters).order_by(*order).offset((page - 1) * size).limit(size)).all()
    return items, total


def require_post(db: Session, post_id: int) -> Post:
    post = db.scalar(select(Post).options(joinedload(Post.location)).where(Post.id == post_id))
    if post is None:
        raise HTTPException(404, "게시글을 찾을 수 없습니다.")
    return post


def increase_post_view(db: Session, post_id: int) -> int:
    post = require_post(db, post_id)
    post.views += 1
    db.commit()
    db.refresh(post)
    return post.views


def create_post(db: Session, data: PostCreate) -> Post:
    if data.location_id is not None and db.get(Location, data.location_id) is None:
        raise HTTPException(400, "존재하지 않는 장소입니다.")
    post = Post(category=data.category, nickname=data.nickname, title=data.title, content=data.content, edit_password=data.password, location_id=data.location_id)
    db.add(post); db.commit(); db.refresh(post)
    return post


def update_post(db: Session, post_id: int, data: PostUpdate) -> Post:
    post = require_post(db, post_id)
    if post.edit_password != data.password:
        raise HTTPException(403, "비밀번호가 일치하지 않습니다.")
    if data.location_id is not None and db.get(Location, data.location_id) is None:
        raise HTTPException(400, "존재하지 않는 장소입니다.")
    post.category, post.nickname, post.title, post.content = data.category, data.nickname, data.title, data.content
    post.location_id = data.location_id
    db.commit(); db.refresh(post)
    return post


def delete_post(db: Session, post_id: int, password: str) -> None:
    post = require_post(db, post_id)
    if post.edit_password != password:
        raise HTTPException(403, "비밀번호가 일치하지 않습니다.")
    db.delete(post); db.commit()
