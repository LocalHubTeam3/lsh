from math import asin, cos, radians, sin, sqrt

from fastapi import HTTPException
from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Location
from app.schemas.ai_feedback import (
    BasketLocationReference,
    RouteAnalysis,
    RouteLeg,
    TravelBasketFeedbackRequest,
    TravelBasketFeedbackResponse,
)
from app.services.llm import generate_text


# 초기 동작용 프롬프트입니다. 서비스 로직과 분리되어 있어 이후 이 값만 교체할 수 있습니다.
BASKET_FEEDBACK_INSTRUCTIONS = (
    "당신은 서울 여행 동선 분석 도우미입니다. 제공된 거리 계산 결과만 근거로 한국어 피드백을 작성하세요. "
    "현재 순서의 장점이나 비효율적인 장거리 구간을 짚고, 추천 순서가 더 짧을 때 변경 이유를 설명하세요. "
    "weather_forecast가 있으면 날짜별 날씨와 기온·강수확률을 요약하고 우산, 겉옷, 물 등 챙기면 좋은 준비물을 근거와 함께 제안하세요. "
    "weather_forecast가 비어 있으면 날씨나 준비물을 추측하지 말고 예보 정보가 없다고 짧게 알리세요. "
    "직선거리임을 분명히 하고 실제 도로 이동거리·이동시간·교통수단은 만들어내지 마세요. "
    "'동선 피드백'과 '날씨·준비물' 두 제목으로 나누어 간결한 글머리표로 작성하세요."
)


def _ordered_locations(db: Session, location_ids: list[int]) -> list[Location]:
    if len(location_ids) != len(set(location_ids)):
        raise HTTPException(400, "중복된 장소가 있습니다.")

    locations = db.scalars(select(Location).where(Location.id.in_(location_ids))).all()
    by_id = {location.id: location for location in locations}
    if set(by_id) != set(location_ids):
        raise HTTPException(400, "존재하지 않는 장소가 있습니다.")
    return [by_id[location_id] for location_id in location_ids]


def _distance_km(first: Location, second: Location) -> float:
    if first.latitude is None or first.longitude is None or second.latitude is None or second.longitude is None:
        raise HTTPException(400, "좌표 정보가 없는 장소는 동선을 분석할 수 없습니다.")
    lat1, lon1, lat2, lon2 = map(radians, (first.latitude, first.longitude, second.latitude, second.longitude))
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1
    value = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    return 6371.0088 * 2 * asin(sqrt(value))


def _route_distance(locations: list[Location]) -> float:
    return sum(_distance_km(first, second) for first, second in zip(locations, locations[1:]))


def _improve_route(route: list[Location]) -> list[Location]:
    best = route[:]
    best_distance = _route_distance(best)
    improved = True
    while improved:
        improved = False
        for start in range(len(best) - 1):
            for end in range(start + 1, len(best)):
                candidate = best[:start] + list(reversed(best[start:end + 1])) + best[end + 1:]
                candidate_distance = _route_distance(candidate)
                if candidate_distance + 1e-9 < best_distance:
                    best, best_distance, improved = candidate, candidate_distance, True
    return best


def recommend_route(locations: list[Location]) -> list[Location]:
    if len(locations) < 3:
        return locations[:]
    candidates = [locations[:]]
    for first in locations:
        remaining = [location for location in locations if location.id != first.id]
        route = [first]
        while remaining:
            next_location = min(remaining, key=lambda item: (_distance_km(route[-1], item), item.id))
            route.append(next_location)
            remaining.remove(next_location)
        candidates.append(_improve_route(route))
    return min(candidates, key=lambda route: (_route_distance(route), [item.id for item in route]))


def _route_analysis(locations: list[Location]) -> RouteAnalysis:
    legs = [
        RouteLeg(
            from_id=first.id, from_title=first.title,
            to_id=second.id, to_title=second.title,
            distance_km=round(_distance_km(first, second), 2),
        )
        for first, second in zip(locations, locations[1:])
    ]
    return RouteAnalysis(
        location_ids=[location.id for location in locations],
        total_distance_km=round(sum(leg.distance_km for leg in legs), 2),
        legs=legs,
    )


async def create_travel_basket_feedback(
    db: Session,
    request: TravelBasketFeedbackRequest,
) -> TravelBasketFeedbackResponse:
    locations = _ordered_locations(db, request.location_ids)
    current_route = _route_analysis(locations)
    recommended_locations = recommend_route(locations)
    recommended_route = _route_analysis(recommended_locations)
    context = [
        {
            "id": location.id,
            "content_id": location.content_id,
            "title": location.title,
            "address": location.address,
            "category": location.category3 or location.category2 or location.category1,
            "longitude": location.longitude,
            "latitude": location.latitude,
        }
        for location in locations
    ]
    feedback = await generate_text(
        instructions=BASKET_FEEDBACK_INSTRUCTIONS,
        payload={
            "user_request": request.request or "선택한 장소 조합을 검토해 주세요.",
            "selected_locations_in_order": context,
            "distance_basis": "장소 좌표 사이의 대권 직선거리(km). 실제 도로 거리나 이동시간이 아님.",
            "current_route": current_route.model_dump(),
            "recommended_route": recommended_route.model_dump(),
            "distance_saved_km": round(max(0, current_route.total_distance_km - recommended_route.total_distance_km), 2),
            "weather_forecast": [item.model_dump(mode="json") for item in request.weather],
        },
        client_factory=AsyncOpenAI,
    )
    return TravelBasketFeedbackResponse(
        feedback=feedback,
        references=[
            BasketLocationReference(id=location.id, title=location.title)
            for location in locations
        ],
        current_route=current_route,
        recommended_route=recommended_route,
        distance_saved_km=round(max(0, current_route.total_distance_km - recommended_route.total_distance_km), 2),
    )
