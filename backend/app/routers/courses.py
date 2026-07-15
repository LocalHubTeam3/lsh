from typing import Literal

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.course import CourseCreate, CourseList, CourseOut, CourseSummary, CourseUpdate, CourseViewCount
from app.schemas.post import PasswordRequest
from app.services import courses as service

router = APIRouter(prefix="/api/courses", tags=["courses"])


def course_out(course) -> CourseOut:
    return CourseOut(
        id=course.id, title=course.title, description=course.description, views=course.views,
        created_at=course.created_at, updated_at=course.updated_at,
        locations=[place.location for place in sorted(course.places, key=lambda item: item.sequence)],
    )


@router.get("", response_model=CourseList)
def list_courses(sort: Literal["latest", "popular"] = "latest", page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)) -> CourseList:
    items, total = service.list_courses(db, sort, page, size)
    return CourseList(items=[CourseSummary.model_validate(item) for item in items], page=page, size=size, total=total)


@router.get("/{course_id}", response_model=CourseOut)
def get_course(course_id: int, db: Session = Depends(get_db)) -> CourseOut:
    return course_out(service.require_course(db, course_id))


@router.post("", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
def create_course(data: CourseCreate, db: Session = Depends(get_db)) -> CourseOut:
    return course_out(service.create_course(db, data))


@router.post("/{course_id}/view", response_model=CourseViewCount)
def increase_course_view(course_id: int, db: Session = Depends(get_db)) -> CourseViewCount:
    return CourseViewCount(views=service.increase_course_view(db, course_id))


@router.put("/{course_id}", response_model=CourseOut)
def update_course(course_id: int, data: CourseUpdate, db: Session = Depends(get_db)) -> CourseOut:
    return course_out(service.update_course(db, course_id, data))


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(course_id: int, data: PasswordRequest, db: Session = Depends(get_db)) -> Response:
    service.delete_course(db, course_id, data.password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
