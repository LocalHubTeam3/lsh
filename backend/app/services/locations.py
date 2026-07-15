from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Location


def list_locations(
    db: Session,
    search: str | None,
    category: str | None,
    content_type: str | None,
    page: int,
    size: int,
):
    filters = []
    if search:
        pattern = f"%{search}%"
        filters.append(or_(Location.title.ilike(pattern), Location.address.ilike(pattern)))
    if category:
        pattern = f"%{category}%"
        filters.append(or_(Location.category1.ilike(pattern), Location.category2.ilike(pattern), Location.category3.ilike(pattern)))
    if content_type:
        filters.append(Location.content_type_id == content_type)
    total = db.scalar(select(func.count(Location.id)).where(*filters)) or 0
    items = db.scalars(
        select(Location).where(*filters).order_by(Location.id).offset((page - 1) * size).limit(size)
    ).all()
    return items, total


def get_location(db: Session, location_id: int) -> Location | None:
    return db.get(Location, location_id)
