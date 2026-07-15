from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Course, CoursePlace, Location
from app.schemas.course import CourseCreate, CourseUpdate


def _validate_locations(db: Session, ids: list[int]) -> None:
    if len(ids) != len(set(ids)):
        raise HTTPException(400, "중복된 장소가 있습니다.")
    found = set(db.scalars(select(Location.id).where(Location.id.in_(ids))).all())
    if found != set(ids):
        raise HTTPException(400, "존재하지 않는 장소가 있습니다.")


def list_courses(db: Session, sort: str, page: int, size: int):
    order = (Course.views.desc(), Course.created_at.desc(), Course.id.desc()) if sort == "popular" else (Course.created_at.desc(), Course.id.desc())
    total = db.scalar(select(func.count(Course.id))) or 0
    items = db.scalars(select(Course).order_by(*order).offset((page - 1) * size).limit(size)).all()
    return items, total


def require_course(db: Session, course_id: int) -> Course:
    course = db.scalar(select(Course).where(Course.id == course_id).options(selectinload(Course.places).selectinload(CoursePlace.location)))
    if course is None:
        raise HTTPException(404, "코스를 찾을 수 없습니다.")
    return course


def create_course(db: Session, data: CourseCreate) -> Course:
    _validate_locations(db, data.location_ids)
    course = Course(title=data.title, description=data.description, edit_password=data.password)
    course.places = [CoursePlace(location_id=value, sequence=index) for index, value in enumerate(data.location_ids, 1)]
    try:
        db.add(course); db.commit(); db.refresh(course)
        return require_course(db, course.id)
    except Exception:
        db.rollback(); raise


def update_course(db: Session, course_id: int, data: CourseUpdate) -> Course:
    course = require_course(db, course_id)
    if course.edit_password != data.password:
        raise HTTPException(403, "비밀번호가 일치하지 않습니다.")
    _validate_locations(db, data.location_ids)
    try:
        course.title, course.description = data.title, data.description
        course.places.clear(); db.flush()
        course.places = [CoursePlace(location_id=value, sequence=index) for index, value in enumerate(data.location_ids, 1)]
        db.commit()
        return require_course(db, course.id)
    except Exception:
        db.rollback(); raise


def delete_course(db: Session, course_id: int, password: str) -> None:
    course = require_course(db, course_id)
    if course.edit_password != password:
        raise HTTPException(403, "비밀번호가 일치하지 않습니다.")
    db.delete(course); db.commit()
