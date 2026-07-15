from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.location import LocationOut


class PostCreate(BaseModel):
    category: str = Field(min_length=1, max_length=50)
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=10000)
    password: str = Field(min_length=1, max_length=100)
    location_id: int | None = Field(default=None, ge=1)


class PostUpdate(PostCreate):
    pass


class PasswordRequest(BaseModel):
    password: str = Field(min_length=1, max_length=100)


class PostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: str
    title: str
    content: str
    views: int
    created_at: datetime
    updated_at: datetime
    location_id: int | None
    location: LocationOut | None


class PostList(BaseModel):
    items: list[PostOut]
    page: int
    size: int
    total: int


class PostViewCount(BaseModel):
    views: int
