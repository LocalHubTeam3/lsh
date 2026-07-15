from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.location import LocationList, LocationOut
from app.services import crowd as crowd_service
from app.services import locations as service

router = APIRouter(prefix="/api/locations", tags=["locations"])


@router.get("", response_model=LocationList)
def list_locations(
    search: str | None = None,
    category: str | None = None,
    content_type: str | None = Query(None, description="TourAPI 콘텐츠 유형 ID (예: 12, 14, 15)"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> LocationList:
    items, total = service.list_locations(db, search, category, content_type, page, size)
    return LocationList(items=items, page=page, size=size, total=total)


@router.get("/{location_id}", response_model=LocationOut)
def get_location(location_id: int, db: Session = Depends(get_db)) -> LocationOut:
    location = service.get_location(db, location_id)
    if location is None:
        raise HTTPException(404, "장소를 찾을 수 없습니다.")
    return LocationOut.model_validate(location)


@router.get("/{location_id}/crowd", response_model=crowd_service.CrowdResponse)
async def get_crowd(location_id: int, db: Session = Depends(get_db)) -> crowd_service.CrowdResponse:
    return await crowd_service.get_crowd(db, location_id)
