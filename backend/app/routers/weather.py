from datetime import date, timedelta

from fastapi import APIRouter, HTTPException, Query

from app.schemas.weather import WeatherForecast
from app.services.weather import get_seoul_forecast


router = APIRouter(prefix="/api/weather", tags=["weather"])


@router.get("/seoul", response_model=WeatherForecast)
async def seoul_weather(
    start_date: date = Query(description="여행 시작일"),
    end_date: date = Query(description="여행 종료일"),
) -> WeatherForecast:
    if end_date < start_date:
        raise HTTPException(400, "종료일은 시작일보다 빠를 수 없습니다.")
    if end_date > start_date + timedelta(days=9):
        raise HTTPException(400, "날씨는 최대 10일까지 조회할 수 있습니다.")
    return await get_seoul_forecast(start_date, end_date)
