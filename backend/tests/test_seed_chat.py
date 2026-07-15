import json

from app.config import get_settings
from app.models import Location
from app.services import chat as chat_service
from scripts.seed_locations import seed_locations


def test_seed_is_idempotent_and_skips_bad_coordinate(db, tmp_path):
    source = tmp_path / "raw"; source.mkdir()
    payload = {"items": [
        {"contentid": "1", "title": "서울숲", "addr1": "", "mapx": "127.1", "mapy": "37.1", "contenttypeid": "12"},
        {"contentid": "2", "title": "오류", "mapx": "not-a-number", "mapy": "37.1"},
    ]}
    (source / "sample.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    first = seed_locations(db, source)
    second = seed_locations(db, source)
    assert (first.total, first.inserted, first.errors) == (2, 1, 1)
    assert (second.inserted, second.duplicate, second.errors) == (0, 1, 1)
    assert db.query(Location).one().address is None


def test_chat_uses_minimized_context(client, db, monkeypatch):
    db.add(Location(content_id="1", title="서울숲", address="서울 성동구", category1="관광")); db.commit()
    settings = get_settings(); monkeypatch.setattr(settings, "openai_api_key", "test-key")
    captured = {}

    class Responses:
        async def create(self, **kwargs):
            captured.update(kwargs)
            return type("Result", (), {"output_text": "서울숲을 추천합니다."})()

    class FakeClient:
        def __init__(self, **kwargs):
            self.responses = Responses()

    monkeypatch.setattr(chat_service, "AsyncOpenAI", FakeClient)
    response = client.post("/api/chat", json={"message": "서울숲 추천", "history": []})
    assert response.status_code == 200
    assert response.json()["references"][0]["title"] == "서울숲"
    assert "edit_password" not in captured["input"] and "test-key" not in captured["input"]


def test_chat_requires_key(client, monkeypatch):
    settings = get_settings(); monkeypatch.setattr(settings, "openai_api_key", "")
    response = client.post("/api/chat", json={"message": "추천", "history": []})
    assert response.status_code == 503
    assert response.json()["detail"] == "OpenAI API 키를 적어야 해요."
