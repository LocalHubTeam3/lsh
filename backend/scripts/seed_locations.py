import json
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal, init_db
from app.models import Location


BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = BACKEND_ROOT / "data" / "raw" / "서울"
@dataclass
class SeedStats:
    total: int = 0
    inserted: int = 0
    duplicate: int = 0
    errors: int = 0


def blank(value: object) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


def optional_float(value: object) -> float | None:
    text = blank(value)
    return float(text) if text is not None else None


def seed_locations(db: Session, source_dir: Path = DEFAULT_SOURCE) -> SeedStats:
    stats = SeedStats()
    existing = set(db.scalars(select(Location.content_id)).all())
    for path in sorted(source_dir.glob("*.json")):
        with path.open(encoding="utf-8") as file:
            payload = json.load(file)
        for item in payload.get("items", []):
            stats.total += 1
            content_id = blank(item.get("contentid"))
            title = blank(item.get("title"))
            if not content_id or not title:
                stats.errors += 1
                continue
            if content_id in existing:
                stats.duplicate += 1
                continue
            try:
                longitude = optional_float(item.get("mapx"))
                latitude = optional_float(item.get("mapy"))
            except (TypeError, ValueError):
                stats.errors += 1
                continue
            db.add(Location(
                content_id=content_id, title=title, address=blank(item.get("addr1")),
                address_detail=blank(item.get("addr2")), longitude=longitude, latitude=latitude,
                image_url=blank(item.get("firstimage")), description=blank(item.get("overview") or item.get("description")), content_type_id=blank(item.get("contenttypeid")),
                category1=blank(item.get("cat1")), category2=blank(item.get("cat2")),
                category3=blank(item.get("cat3")), crowd_area_code=None, crowd_area_name=None,
            ))
            existing.add(content_id)
            stats.inserted += 1
    db.commit()
    return stats


def main() -> None:
    init_db()
    with SessionLocal() as db:
        stats = seed_locations(db)
    print(f"전체: {stats.total}")
    print(f"신규 저장: {stats.inserted}")
    print(f"중복: {stats.duplicate}")
    print(f"오류: {stats.errors}")


if __name__ == "__main__":
    main()
