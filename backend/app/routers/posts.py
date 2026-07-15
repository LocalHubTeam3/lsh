from typing import Literal

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.post import PasswordRequest, PostCreate, PostList, PostOut, PostUpdate, PostViewCount
from app.services import posts as service

router = APIRouter(prefix="/api/posts", tags=["posts"])


@router.get("", response_model=PostList)
def list_posts(search: str | None = None, search_field: Literal["all", "title", "content", "nickname"] = "all", category: str | None = None, location_id: int | None = Query(None, ge=1), sort: Literal["latest", "views"] = "latest", page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)) -> PostList:
    items, total = service.list_posts(db, search, search_field, category, location_id, sort, page, size)
    return PostList(items=items, page=page, size=size, total=total)


@router.get("/{post_id}", response_model=PostOut)
def get_post(post_id: int, db: Session = Depends(get_db)) -> PostOut:
    return PostOut.model_validate(service.require_post(db, post_id))


@router.post("", response_model=PostOut, status_code=status.HTTP_201_CREATED)
def create_post(data: PostCreate, db: Session = Depends(get_db)) -> PostOut:
    return PostOut.model_validate(service.create_post(db, data))


@router.post("/{post_id}/view", response_model=PostViewCount)
def increase_post_view(post_id: int, db: Session = Depends(get_db)) -> PostViewCount:
    return PostViewCount(views=service.increase_post_view(db, post_id))


@router.put("/{post_id}", response_model=PostOut)
def update_post(post_id: int, data: PostUpdate, db: Session = Depends(get_db)) -> PostOut:
    return PostOut.model_validate(service.update_post(db, post_id, data))


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, data: PasswordRequest, db: Session = Depends(get_db)) -> Response:
    service.delete_post(db, post_id, data.password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
