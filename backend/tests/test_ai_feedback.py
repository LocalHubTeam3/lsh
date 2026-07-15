import json

from app.config import get_settings
from app.models import Location
from app.services import ai_feedback as feedback_service


def _location(content_id: str, title: str, longitude: float) -> Location:
    return Location(
        content_id=content_id,
        title=title,
        address="서울",
        longitude=longitude,
        latitude=37.5,
        category1="관광",
    )


def test_travel_basket_feedback_preserves_order_and_minimizes_context(client, db, monkeypatch):
    first = _location("source-1", "첫 번째 장소", 127.1)
    second = _location("source-2", "두 번째 장소", 127.2)
    db.add_all([first, second])
    db.commit()
    settings = get_settings()
    monkeypatch.setattr(settings, "openai_api_key", "test-key")
    monkeypatch.setattr(settings, "openai_model", "gpt-5-mini")
    captured = {}

    class Responses:
        async def create(self, **kwargs):
            captured.update(kwargs)
            return type("Result", (), {"output_text": "하루 일정으로 검토했습니다."})()

    class FakeClient:
        def __init__(self, **kwargs):
            captured["client_options"] = kwargs
            self.responses = Responses()

    monkeypatch.setattr(feedback_service, "AsyncOpenAI", FakeClient)
    response = client.post(
        "/api/ai/travel-basket-feedback",
        json={
            "location_ids": [second.id, first.id],
            "request": "동선을 봐줘",
            "weather": [{
                "date": "2026-07-16", "forecast_type": "short", "condition": "비",
                "temperature_min": 24, "temperature_max": 31,
                "precipitation_probability": 60,
            }],
        },
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["references"]] == [second.id, first.id]
    assert response.json()["current_route"]["location_ids"] == [second.id, first.id]
    assert response.json()["current_route"]["total_distance_km"] > 0
    assert response.json()["current_route"]["legs"][0]["from_id"] == second.id
    payload = json.loads(captured["input"])
    assert [item["id"] for item in payload["selected_locations_in_order"]] == [second.id, first.id]
    assert payload["weather_forecast"][0]["condition"] == "비"
    assert payload["weather_forecast"][0]["precipitation_probability"] == 60
    assert "edit_password" not in captured["input"]
    assert "test-key" not in captured["input"]
    assert captured["model"] == "gpt-5-mini"
    assert captured["client_options"]["timeout"] == settings.openai_timeout
    assert captured["client_options"]["max_retries"] == 0


def test_route_recommendation_reduces_backtracking(db):
    first = _location("source-1", "서쪽", 127.0)
    middle = _location("source-2", "중간", 127.1)
    east = _location("source-3", "동쪽", 127.2)
    db.add_all([first, middle, east])
    db.commit()

    recommended = feedback_service.recommend_route([first, east, middle])

    assert [item.id for item in recommended] in ([first.id, middle.id, east.id], [east.id, middle.id, first.id])


def test_travel_basket_feedback_rejects_duplicate_and_missing_locations(client, db):
    location = _location("source-1", "장소", 127.1)
    db.add(location)
    db.commit()

    duplicate = client.post(
        "/api/ai/travel-basket-feedback",
        json={"location_ids": [location.id, location.id]},
    )
    missing = client.post(
        "/api/ai/travel-basket-feedback",
        json={"location_ids": [location.id, 9999]},
    )

    assert duplicate.status_code == 400
    assert missing.status_code == 400


def test_travel_basket_feedback_requires_api_key(client, db, monkeypatch):
    location = _location("source-1", "장소", 127.1)
    db.add(location)
    db.commit()
    settings = get_settings()
    monkeypatch.setattr(settings, "openai_api_key", "")

    response = client.post(
        "/api/ai/travel-basket-feedback",
        json={"location_ids": [location.id]},
    )

    assert response.status_code == 503


def test_travel_basket_feedback_maps_openai_failure_to_502(client, db, monkeypatch):
    location = _location("source-1", "장소", 127.1)
    db.add(location)
    db.commit()
    settings = get_settings()
    monkeypatch.setattr(settings, "openai_api_key", "test-key")

    class BrokenClient:
        def __init__(self, **kwargs):
            raise RuntimeError("provider unavailable")

    monkeypatch.setattr(feedback_service, "AsyncOpenAI", BrokenClient)
    response = client.post(
        "/api/ai/travel-basket-feedback",
        json={"location_ids": [location.id]},
    )

    assert response.status_code == 502
