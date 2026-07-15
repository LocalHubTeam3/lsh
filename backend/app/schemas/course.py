from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.location import LocationOut


class CourseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=10000)
    password: str = Field(min_length=1, max_length=100)
    location_ids: list[int] = Field(min_length=2, max_length=100)


class CourseUpdate(CourseCreate):
    pass


class CourseSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    views: int
    created_at: datetime
    updated_at: datetime


class CourseOut(CourseSummary):
    locations: list[LocationOut]


class CourseList(BaseModel):
    items: list[CourseSummary]
    page: int
    size: int
    total: int


class CourseViewCount(BaseModel):
    views: int
