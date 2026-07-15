from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
import asyncio
import logging
from typing import Any
from urllib.parse import unquote

import httpx
from fastapi import HTTPException

from app.config import get_settings
from app.schemas.weather import DailyWeather, WeatherForecast


KST = timezone(timedelta(hours=9))
KMA_SHORT_FORECAST_URL = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
KMA_MID_LAND_URL = "https://apis.data.go.kr/1360000/MidFcstInfoService/getMidLandFcst"
KMA_MID_TEMPERATURE_URL = "https://apis.data.go.kr/1360000/MidFcstInfoService/getMidTa"
SEOUL_GRID = (60, 127)
SEOUL_LAND_REGION = "11B00000"
SEOUL_TEMPERATURE_REGION = "11B10101"
BASE_TIMES = (2, 5, 8, 11, 14, 17, 20, 23)
SKY_LABELS = {"1": "맑음", "3": "구름 많음", "4": "흐림"}
PTY_LABELS = {"1": "비", "2": "비 또는 눈", "3": "눈", "4": "소나기"}
logger = logging.getLogger(__name__)


class WeatherFetchError(Exception):
    """The KMA response could not be fetched or parsed."""


def latest_base_datetime(now: datetime | None = None) -> datetime:
    current = (now or datetime.now(KST)).astimezone(KST) - timedelta(minutes=10)
    candidates = [
        datetime.combine(current.date(), time(hour=hour), tzinfo=KST)
        for hour in BASE_TIMES
        if hour <= current.hour
    ]
    if candidates:
        return candidates[-1]
    return datetime.combine(current.date() - timedelta(days=1), time(hour=23), tzinfo=KST)


def latest_mid_base_datetime(now: datetime | None = None) -> datetime:
    current = (now or datetime.now(KST)).astimezone(KST) - timedelta(minutes=10)
    if current.hour >= 18:
        hour = 18
    elif current.hour >= 6:
        hour = 6
    else:
        return datetime.combine(current.date() - timedelta(days=1), time(hour=18), tzinfo=KST)
    return datetime.combine(current.date(), time(hour=hour), tzinfo=KST)


def _number(value: object) -> float | None:
    try:
        return float(str(value).replace("℃", "").strip())
    except (TypeError, ValueError):
        return None


def _value_near_noon(values: list[dict[str, str]]) -> str | None:
    if not values:
        return None
    return min(values, key=lambda item: abs(int(item.get("fcstTime", "1200")) - 1200)).get("fcstValue")


def aggregate_daily(items: list[dict[str, Any]], start_date: date, end_date: date) -> list[DailyWeather]:
    grouped: dict[str, dict[str, list[dict[str, str]]]] = defaultdict(lambda: defaultdict(list))
    for item in items:
        forecast_date = str(item.get("fcstDate", ""))
        category = str(item.get("category", ""))
        if forecast_date and category:
            grouped[forecast_date][category].append({
                "fcstTime": str(item.get("fcstTime", "")),
                "fcstValue": str(item.get("fcstValue", "")),
            })

    result: list[DailyWeather] = []
    current = start_date
    while current <= end_date:
        categories = grouped.get(current.strftime("%Y%m%d"))
        if categories:
            temperatures = [_number(item["fcstValue"]) for item in categories.get("TMP", [])]
            temperatures = [value for value in temperatures if value is not None]
            minimum = _number(_value_near_noon(categories.get("TMN", [])))
            maximum = _number(_value_near_noon(categories.get("TMX", [])))
            rain_types = [item["fcstValue"] for item in categories.get("PTY", []) if item["fcstValue"] != "0"]
            sky = _value_near_noon(categories.get("SKY", []))
            condition = PTY_LABELS.get(rain_types[0], "강수") if rain_types else SKY_LABELS.get(sky or "", "날씨 정보")
            probabilities = [_number(item["fcstValue"]) for item in categories.get("POP", [])]
            humidity = _number(_value_near_noon(categories.get("REH", [])))
            wind = [_number(item["fcstValue"]) for item in categories.get("WSD", [])]
            result.append(DailyWeather(
                date=current,
                forecast_type="short",
                condition=condition,
                temperature_min=minimum if minimum is not None else (min(temperatures) if temperatures else None),
                temperature_max=maximum if maximum is not None else (max(temperatures) if temperatures else None),
                precipitation_probability=int(max(value for value in probabilities if value is not None)) if any(value is not None for value in probabilities) else None,
                humidity=int(humidity) if humidity is not None else None,
                wind_speed=max((value for value in wind if value is not None), default=None),
            ))
        current += timedelta(days=1)
    return result


def aggregate_mid_daily(
    land_item: dict[str, Any],
    temperature_item: dict[str, Any],
    base_date: date,
    start_date: date,
    end_date: date,
) -> list[DailyWeather]:
    result: list[DailyWeather] = []
    for offset in range(3, 11):
        forecast_date = base_date + timedelta(days=offset)
        if not start_date <= forecast_date <= end_date:
            continue
        suffixes = [str(offset)] if offset >= 8 else [f"{offset}Am", f"{offset}Pm"]
        conditions = [str(land_item.get(f"wf{suffix}") or "").strip() for suffix in suffixes]
        conditions = [value for value in conditions if value]
        probabilities = [_number(land_item.get(f"rnSt{suffix}")) for suffix in suffixes]
        probabilities = [value for value in probabilities if value is not None]
        if not conditions and not probabilities and temperature_item.get(f"taMin{offset}") is None:
            continue
        condition = " / ".join(dict.fromkeys(conditions)) if conditions else "날씨 정보"
        result.append(DailyWeather(
            date=forecast_date,
            forecast_type="mid",
            condition=condition,
            temperature_min=_number(temperature_item.get(f"taMin{offset}")),
            temperature_max=_number(temperature_item.get(f"taMax{offset}")),
            precipitation_probability=int(max(probabilities)) if probabilities else None,
        ))
    return result


async def _fetch_items(url: str, params: dict[str, object], timeout: float, source: str) -> list[dict[str, Any]]:
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()
        api_response = payload.get("response", {})
        header = api_response.get("header", {})
        if str(header.get("resultCode")) != "00":
            raise WeatherFetchError(str(header.get("resultMsg") or "api_error"))
        items = api_response.get("body", {}).get("items", {}).get("item", [])
        if not isinstance(items, list):
            raise WeatherFetchError("unexpected_items")
        return items
    except (httpx.HTTPError, ValueError, TypeError, AttributeError, WeatherFetchError) as exc:
        logger.warning("KMA %s forecast failed: reason=%s", source, type(exc).__name__)
        raise WeatherFetchError(source) from None


async def _get_short_forecast(service_key: str, start_date: date, end_date: date, timeout: float) -> tuple[datetime, list[DailyWeather]]:
    base = latest_base_datetime()
    params = {
        "serviceKey": unquote(service_key.strip()), "pageNo": 1, "numOfRows": 1000, "dataType": "JSON",
        "base_date": base.strftime("%Y%m%d"), "base_time": base.strftime("%H%M"),
        "nx": SEOUL_GRID[0], "ny": SEOUL_GRID[1],
    }
    items = await _fetch_items(KMA_SHORT_FORECAST_URL, params, timeout, "short")
    return base, aggregate_daily(items, start_date, end_date)


async def _get_mid_forecast(service_key: str, start_date: date, end_date: date, timeout: float) -> tuple[datetime, list[DailyWeather]]:
    base = latest_mid_base_datetime()
    common = {
        "serviceKey": unquote(service_key.strip()), "pageNo": 1, "numOfRows": 10,
        "dataType": "JSON", "tmFc": base.strftime("%Y%m%d%H%M"),
    }
    land_task = _fetch_items(KMA_MID_LAND_URL, {**common, "regId": SEOUL_LAND_REGION}, timeout, "mid_land")
    temperature_task = _fetch_items(KMA_MID_TEMPERATURE_URL, {**common, "regId": SEOUL_TEMPERATURE_REGION}, timeout, "mid_temperature")
    land_items, temperature_items = await asyncio.gather(land_task, temperature_task)
    land = land_items[0] if land_items else {}
    temperature = temperature_items[0] if temperature_items else {}
    return base, aggregate_mid_daily(land, temperature, base.date(), start_date, end_date)


async def get_seoul_forecast(start_date: date, end_date: date) -> WeatherForecast:
    settings = get_settings()
    short_key = settings.kma_short_service_key or settings.kma_service_key
    mid_key = settings.kma_mid_service_key or settings.kma_service_key
    if not short_key and not mid_key:
        raise HTTPException(503, "기상청 API 키가 설정되지 않았습니다.")
    today = datetime.now(KST).date()
    tasks = []
    if short_key and start_date <= today + timedelta(days=4):
        tasks.append(_get_short_forecast(short_key, start_date, end_date, settings.external_api_timeout))
    if mid_key and end_date >= today + timedelta(days=3):
        tasks.append(_get_mid_forecast(mid_key, start_date, end_date, settings.external_api_timeout))
    if not tasks:
        missing = "중기" if start_date > today + timedelta(days=4) else "단기"
        raise HTTPException(503, f"기상청 {missing}예보 API 키가 설정되지 않았습니다.")
    try:
        forecasts = await asyncio.gather(*tasks)
    except WeatherFetchError:
        raise HTTPException(502, "기상청 날씨 정보를 가져오지 못했습니다. API 키와 서비스 상태를 확인해 주세요.") from None
    merged: dict[date, DailyWeather] = {}
    base = forecasts[0][0]
    for _, items in reversed(forecasts):
        for item in items:
            merged[item.date] = item
    return WeatherForecast(
        location="서울",
        base_datetime=base,
        items=sorted(merged.values(), key=lambda item: item.date),
    )
