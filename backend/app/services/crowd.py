from datetime import datetime, timedelta, timezone
import logging
import re
from urllib.parse import quote

import httpx
from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import CrowdCache, Location


NOTICE = "통신 데이터를 기반으로 한 추정값이며 실제 인구와 다를 수 있습니다."
SEOUL_WEB_API = "https://data.seoul.go.kr/SeoulRtd/api"
logger = logging.getLogger(__name__)


class CrowdFetchError(Exception):
    """External crowd source failed without retaining a secret-bearing URL."""


class CrowdNotAvailable(Exception):
    """The requested exact place is not a Seoul real-time hotspot."""


class CrowdResponse(BaseModel):
    available: bool
    location_id: int
    area_code: str | None = None
    area_name: str | None = None
    congestion_level: str | None = None
    population_min: int | None = None
    population_max: int | None = None
    population_estimate: int | None = None
    updated_at: datetime | None = None
    notice: str


def _response(location_id: int, cache: CrowdCache) -> CrowdResponse:
    estimate = None
    if cache.population_min is not None and cache.population_max is not None:
        estimate = (cache.population_min + cache.population_max) // 2
    return CrowdResponse(
        available=True, location_id=location_id, area_code=None, area_name=cache.area_name,
        congestion_level=cache.congestion_level, population_min=cache.population_min,
        population_max=cache.population_max, population_estimate=estimate,
        updated_at=cache.source_updated_at or cache.cached_at, notice=NOTICE,
    )


def _parse_time(value: object) -> datetime | None:
    if not value:
        return None
    text = str(value)
    for fmt in ("%Y-%m-%d %H:%M", "%Y%m%d%H%M%S"):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=timezone(timedelta(hours=9)))
        except ValueError:
            continue
    return None


def _first_dict(payload: object) -> dict[str, object]:
    if isinstance(payload, list):
        if not payload:
            raise CrowdNotAvailable
        if isinstance(payload[0], dict):
            return payload[0]
    if isinstance(payload, dict):
        return payload
    raise CrowdFetchError("unexpected_response_shape")


def _pipe_values(value: object) -> list[str]:
    return str(value or "").split("|") if value else []


def _current_index(trend: dict[str, object]) -> int:
    labels = _pipe_values(trend.get("time_cd"))
    for index, label in enumerate(labels):
        if "현재" in label:
            return index
    return min(12, max(0, len(labels) - 1))


def _population_range(interval: str) -> tuple[int | None, int | None]:
    # The Seoul web response has used both comma and slash thousands separators.
    normalized = interval.replace(",", "").replace("/", "")
    numbers = [int(value) for value in re.findall(r"\d+", normalized)]
    if len(numbers) >= 2:
        return numbers[0], numbers[1]
    return None, None


async def fetch_seoul_web_crowd(area_name: str, timeout: float, now: datetime) -> dict[str, object]:
    headers = {
        "Accept": "application/json",
        "Referer": "https://data.seoul.go.kr/SeoulRtd/map",
        "User-Agent": "LocalHub/1.0",
    }
    try:
        async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
            report_response = await client.get(f"{SEOUL_WEB_API}/ppltn", params={"hotspotNm": area_name})
            trend_response = await client.get(f"{SEOUL_WEB_API}/ppltn_congest", params={"hotspotNm": area_name})
            report_response.raise_for_status()
            trend_response.raise_for_status()
            report = _first_dict(report_response.json())
            trend = _first_dict(trend_response.json())
    except (CrowdFetchError, CrowdNotAvailable):
        raise
    except httpx.HTTPStatusError as exc:
        raise CrowdFetchError(f"http_status_{exc.response.status_code}") from None
    except (httpx.HTTPError, ValueError, TypeError) as exc:
        raise CrowdFetchError(type(exc).__name__) from None

    index = _current_index(trend)
    intervals = _pipe_values(trend.get("people_interval"))
    congestion_levels = _pipe_values(trend.get("congestion_label_list"))
    interval = intervals[index] if index < len(intervals) else ""
    population_min, population_max = _population_range(interval)
    congestion_level = str(report.get("congestion_text") or "").strip()
    if not congestion_level and index < len(congestion_levels):
        congestion_level = congestion_levels[index].strip()
    if not congestion_level and population_min is None:
        raise CrowdFetchError("missing_current_population")
    return {
        "area_name": str(report.get("hotspot_nm") or area_name),
        "congestion_level": congestion_level or None,
        "population_min": population_min,
        "population_max": population_max,
        "source_updated_at": now,
        "cached_at": now,
    }


async def fetch_seoul_openapi_crowd(
    area_name: str,
    api_key: str,
    timeout: float,
    now: datetime,
) -> dict[str, object]:
    url = f"http://openapi.seoul.go.kr:8088/{api_key}/json/citydata/1/5/{quote(area_name, safe='')}"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            payload = response.json()
        citydata = payload.get("CITYDATA") or payload.get("citydata") or {}
        if isinstance(citydata, list):
            citydata = citydata[0] if citydata else {}
        population = citydata.get("LIVE_PPLTN_STTS") or []
        population = population[0] if isinstance(population, list) and population else {}
        if not population:
            raise CrowdNotAvailable
        return {
            "area_name": citydata.get("AREA_NM") or area_name,
            "congestion_level": population.get("AREA_CONGEST_LVL"),
            "population_min": int(population["AREA_PPLTN_MIN"]) if population.get("AREA_PPLTN_MIN") else None,
            "population_max": int(population["AREA_PPLTN_MAX"]) if population.get("AREA_PPLTN_MAX") else None,
            "source_updated_at": _parse_time(population.get("PPLTN_TIME")),
            "cached_at": now,
        }
    except (CrowdFetchError, CrowdNotAvailable):
        raise
    except httpx.HTTPStatusError as exc:
        raise CrowdFetchError(f"http_status_{exc.response.status_code}") from None
    except (httpx.HTTPError, ValueError, TypeError, KeyError) as exc:
        raise CrowdFetchError(type(exc).__name__) from None


async def get_crowd(db: Session, location_id: int) -> CrowdResponse:
    location = db.get(Location, location_id)
    if location is None:
        raise HTTPException(404, "장소를 찾을 수 없습니다.")

    # Every clicked place is checked by its exact TourAPI title. Do not substitute
    # a nearby manually mapped hotspot, because that would describe another area.
    query_name = location.title
    cache_key = f"WEB:{location.content_id}"

    now = datetime.now(timezone.utc)
    cached = db.get(CrowdCache, cache_key)
    if cached:
        cached_at = cached.cached_at if cached.cached_at.tzinfo else cached.cached_at.replace(tzinfo=timezone.utc)
        if now - cached_at < timedelta(minutes=5):
            return _response(location_id, cached)

    settings = get_settings()
    try:
        values = await fetch_seoul_web_crowd(
            query_name,
            settings.external_api_timeout,
            now,
        )
    except CrowdNotAvailable:
        return CrowdResponse(
            available=False,
            location_id=location_id,
            area_code=None,
            area_name=query_name,
            notice="이 장소 자체의 서울시 실시간 혼잡도 데이터가 없어요.",
        )
    except CrowdFetchError as web_error:
        logger.warning(
            "Seoul HTTPS crowd source failed: area=%s reason=%s",
            query_name,
            web_error,
        )
        if not settings.seoul_api_key:
            raise HTTPException(503, "서울시 API 키를 적어야 해요.") from None
        try:
            values = await fetch_seoul_openapi_crowd(
                query_name,
                settings.seoul_api_key,
                settings.external_api_timeout,
                now,
            )
        except CrowdNotAvailable:
            return CrowdResponse(
                available=False,
                location_id=location_id,
                area_code=None,
                area_name=query_name,
                notice="이 장소 자체의 서울시 실시간 혼잡도 데이터가 없어요.",
            )
        except CrowdFetchError as openapi_error:
            logger.warning(
                "Seoul OpenAPI crowd fallback failed: area=%s reason=%s",
                query_name,
                openapi_error,
            )
            raise HTTPException(502, "서울시 실시간 인구 정보를 가져오지 못했습니다.") from None

    if cached is None:
        cached = CrowdCache(area_code=cache_key, **values)
        db.add(cached)
    else:
        for key, value in values.items():
            setattr(cached, key, value)
    db.commit(); db.refresh(cached)
    return _response(location_id, cached)
