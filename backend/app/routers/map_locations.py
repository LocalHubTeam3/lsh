from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.map import MapLocationList, MapSearchList
from app.services.map_locations import get_map_locations, search_map_locations

router = APIRouter(prefix="/api/map", tags=["map"])
ContentType = Literal["12", "14", "15", "25", "28", "32", "38"]


@router.get("/locations", response_model=MapLocationList)
def map_locations(
    content_type: ContentType = Query(description="선택한 원본 JSON의 TourAPI 콘텐츠 유형 ID"),
    db: Session = Depends(get_db),
) -> MapLocationList:
    items = get_map_locations(db, content_type)
    return MapLocationList(items=items, total=len(items), content_type=content_type)


@router.get("/search", response_model=MapSearchList)
def search_locations(
    query: str = Query(min_length=1, max_length=100, description="장소명에 포함될 검색어"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> MapSearchList:
    normalized_query = query.strip()
    if not normalized_query:
        return MapSearchList(items=[], total=0, query="")
    items, total = search_map_locations(db, normalized_query, limit)
    return MapSearchList(items=items, total=total, query=normalized_query)
