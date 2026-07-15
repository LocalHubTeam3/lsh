from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models import Location


def get_map_locations(db: Session, content_type: str) -> list[Location]:
    return list(
        db.scalars(
            select(Location)
            .where(
                Location.content_type_id == content_type,
                Location.latitude.is_not(None),
                Location.longitude.is_not(None),
            )
            .order_by(Location.id)
        ).all()
    )


def search_map_locations(db: Session, query: str, limit: int) -> tuple[list[Location], int]:
    escaped_query = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    pattern = f"%{escaped_query}%"
    filters = (
        Location.title.ilike(pattern, escape="\\"),
        Location.latitude.is_not(None),
        Location.longitude.is_not(None),
    )
    total = db.scalar(select(func.count(Location.id)).where(*filters)) or 0
    items = list(
        db.scalars(
            select(Location)
            .where(*filters)
            .order_by(case((Location.title == query, 0), else_=1), Location.title, Location.id)
            .limit(limit)
        ).all()
    )
    return items, total
