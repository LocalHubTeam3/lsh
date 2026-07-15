from datetime import datetime, timezone

from app.config import Settings, get_settings
from app.models import CrowdCache, Location
from app.services import crowd as crowd_service


def locations(db):
    values = [
        Location(content_id="1", title="서울숲", address="서울 성동구", longitude=127.0, latitude=37.5, category1="관광", content_type_id="12", image_url="https://example.com/forest.jpg"),
        Location(content_id="2", title="경복궁", address="서울 종로구", longitude=126.9, latitude=37.6, category1="역사", content_type_id="12"),
        Location(content_id="3", title="광화문광장", address="서울 종로구", longitude=126.97, latitude=37.57, category1="관광", content_type_id="14"),
    ]
    db.add_all(values); db.commit()
    return values


def test_health_and_openapi(client):
    assert client.get("/api/health").json() == {"status": "ok"}
    assert client.get("/").json()["service"] == "LocalHub API"
    paths = client.get("/openapi.json").json()["paths"]
    assert {"/api/locations", "/api/posts", "/api/courses", "/api/chat"} <= set(paths)


def test_feature_status_does_not_expose_keys(client, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "openai_api_key", "secret-openai")
    monkeypatch.setattr(settings, "seoul_api_key", "secret-seoul")
    response = client.get("/api/features")
    assert response.json() == {"openai_api_configured": True, "seoul_api_configured": True}
    assert "secret" not in response.text


def test_map_page_and_map_locations(client, db):
    locations(db)
    response = client.get("/api/map/locations", params={"content_type": "12"})
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert response.json()["items"][0]["image_url"] == "https://example.com/forest.jpg"
    assert client.get("/api/map/locations", params={"content_type": "39"}).status_code == 422


def test_map_search_matches_place_name_substring(client, db):
    locations(db)

    response = client.get("/api/map/search", params={"query": "광화"})
    assert response.status_code == 200
    assert response.json()["query"] == "광화"
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["title"] == "광화문광장"

    assert client.get("/api/map/search", params={"query": "궁"}).json()["total"] == 1
    assert client.get("/api/map/search", params={"query": "없는 장소"}).json()["items"] == []
    assert client.get("/api/map/search", params={"query": "   "}).json()["total"] == 0
    assert client.get("/api/map/search", params={"query": "서울", "limit": 101}).status_code == 422


def test_comma_separated_cors_origins(monkeypatch):
    monkeypatch.setenv("FRONTEND_ORIGINS", "https://one.example,https://two.example")
    assert Settings().frontend_origins == ["https://one.example", "https://two.example"]


def test_location_search_pagination_and_404(client, db):
    locations(db)
    response = client.get("/api/locations", params={"search": "서울", "category": "관광", "size": 1})
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert response.json()["items"][0]["longitude"] == 127.0
    assert client.get("/api/locations/999").status_code == 404
    assert client.get("/api/locations", params={"size": 101}).status_code == 422
    assert client.get("/api/locations", params={"content_type": "999"}).json()["total"] == 0


def test_post_crud_password_and_views(client):
    payload = {"category": "질문", "title": "서울숲 질문", "content": "어디로 가나요", "password": "1234"}
    created = client.post("/api/posts", json=payload)
    assert created.status_code == 201
    post_id = created.json()["id"]
    assert "edit_password" not in created.text and "password" not in created.json()
    assert client.get(f"/api/posts/{post_id}").json()["views"] == 1
    wrong = {**payload, "title": "수정", "password": "wrong"}
    assert client.put(f"/api/posts/{post_id}", json=wrong).status_code == 403
    updated = client.put(f"/api/posts/{post_id}", json={**payload, "title": "수정"})
    assert updated.json()["title"] == "수정"
    assert client.request("DELETE", f"/api/posts/{post_id}", json={"password": "wrong"}).status_code == 403
    assert client.request("DELETE", f"/api/posts/{post_id}", json={"password": "1234"}).status_code == 204


def test_post_location_relation_and_filters(client, db):
    places = locations(db)
    first = {"category": "질문", "title": "서울숲 질문", "content": "산책", "password": "1234", "location_id": places[0].id}
    second = {"category": "후기", "title": "경복궁 후기", "content": "관람", "password": "1234", "location_id": places[1].id}
    created = client.post("/api/posts", json=first)
    assert created.status_code == 201
    assert created.json()["location"]["title"] == "서울숲"
    assert client.post("/api/posts", json={**first, "location_id": 999}).status_code == 400
    assert client.post("/api/posts", json=second).status_code == 201
    assert client.get("/api/posts", params={"category": "질문"}).json()["total"] == 1
    related = client.get("/api/posts", params={"location_id": places[0].id}).json()
    assert related["total"] == 1
    assert related["items"][0]["location_id"] == places[0].id


def test_course_crud_order_and_validation(client, db):
    ids = [item.id for item in locations(db)]
    base = {"title": "나들이", "description": "서울 코스", "password": "1234", "location_ids": ids[:2]}
    assert client.post("/api/courses", json={**base, "location_ids": [ids[0], ids[0]]}).status_code == 400
    assert client.post("/api/courses", json={**base, "location_ids": [ids[0], 999]}).status_code == 400
    created = client.post("/api/courses", json=base)
    assert created.status_code == 201
    course_id = created.json()["id"]
    assert [item["id"] for item in created.json()["locations"]] == ids[:2]
    changed = {**base, "location_ids": list(reversed(ids[1:])), "description": "변경"}
    updated = client.put(f"/api/courses/{course_id}", json=changed)
    assert [item["id"] for item in updated.json()["locations"]] == list(reversed(ids[1:]))
    assert "password" not in updated.text
    assert client.request("DELETE", f"/api/courses/{course_id}", json={"password": "1234"}).status_code == 204


def test_crowd_unmapped_and_cached(client, db, monkeypatch):
    async def unavailable(*_args):
        raise crowd_service.CrowdNotAvailable

    monkeypatch.setattr(crowd_service, "fetch_seoul_web_crowd", unavailable)
    place = Location(content_id="10", title="일반 장소", address=None)
    mapped = Location(content_id="11", title="경복궁", address=None, crowd_area_code="POI009", crowd_area_name="경복궁")
    db.add_all([place, mapped]); db.commit()
    db.add(CrowdCache(area_code="WEB:11", area_name="경복궁", congestion_level="보통", population_min=1000, population_max=2000, source_updated_at=datetime.now(timezone.utc), cached_at=datetime.now(timezone.utc)))
    db.commit()
    unavailable_response = client.get(f"/api/locations/{place.id}/crowd").json()
    assert unavailable_response["available"] is False
    assert unavailable_response["area_name"] == "일반 장소"
    result = client.get(f"/api/locations/{mapped.id}/crowd")
    assert result.status_code == 200
    assert result.json()["population_estimate"] == 1500


def test_crowd_missing_api_key_has_friendly_message(client, db, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "seoul_api_key", "")
    async def failed_web(*_args):
        raise crowd_service.CrowdFetchError("ConnectTimeout")

    monkeypatch.setattr(crowd_service, "fetch_seoul_web_crowd", failed_web)
    place = Location(content_id="20", title="서울숲", address=None, crowd_area_code="POI013", crowd_area_name="서울숲공원")
    db.add(place); db.commit()
    response = client.get(f"/api/locations/{place.id}/crowd")
    assert response.status_code == 503
    assert response.json()["detail"] == "서울시 API 키를 적어야 해요."


def test_crowd_uses_https_source_without_api_key(client, db, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "seoul_api_key", "")

    async def successful_web(area_name, _timeout, now):
        assert area_name == "경복궁"
        return {
            "area_name": area_name,
            "congestion_level": "보통",
            "population_min": 1500,
            "population_max": 2000,
            "source_updated_at": now,
            "cached_at": now,
        }

    monkeypatch.setattr(crowd_service, "fetch_seoul_web_crowd", successful_web)
    place = Location(content_id="21", title="경복궁", address=None, crowd_area_code="POI009", crowd_area_name="경복궁")
    db.add(place); db.commit()
    response = client.get(f"/api/locations/{place.id}/crowd")
    assert response.status_code == 200
    assert response.json()["congestion_level"] == "보통"
    assert response.json()["population_estimate"] == 1750


def test_crowd_falls_back_to_keyed_openapi(client, db, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "seoul_api_key", "test-key")

    async def failed_web(*_args):
        raise crowd_service.CrowdFetchError("ConnectTimeout")

    async def successful_openapi(area_name, api_key, _timeout, now):
        assert api_key == "test-key"
        return {
            "area_name": area_name,
            "congestion_level": "여유",
            "population_min": 400,
            "population_max": 500,
            "source_updated_at": now,
            "cached_at": now,
        }

    monkeypatch.setattr(crowd_service, "fetch_seoul_web_crowd", failed_web)
    monkeypatch.setattr(crowd_service, "fetch_seoul_openapi_crowd", successful_openapi)
    place = Location(content_id="22", title="경복궁", address=None, crowd_area_code="POI009", crowd_area_name="경복궁")
    db.add(place); db.commit()
    response = client.get(f"/api/locations/{place.id}/crowd")
    assert response.status_code == 200
    assert response.json()["population_estimate"] == 450


def test_crowd_queries_clicked_title_not_manual_mapping(client, db, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "seoul_api_key", "")

    async def exact_title_web(area_name, _timeout, now):
        assert area_name == "광화문광장"
        return {
            "area_name": area_name,
            "congestion_level": "보통",
            "population_min": 1000,
            "population_max": 1500,
            "source_updated_at": now,
            "cached_at": now,
        }

    monkeypatch.setattr(crowd_service, "fetch_seoul_web_crowd", exact_title_web)
    place = Location(
        content_id="23",
        title="광화문광장",
        address=None,
        crowd_area_code="POI008",
        crowd_area_name="광화문·덕수궁",
    )
    db.add(place); db.commit()
    response = client.get(f"/api/locations/{place.id}/crowd")
    assert response.status_code == 200
    assert response.json()["area_name"] == "광화문광장"
