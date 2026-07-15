from datetime import date, datetime, timedelta, timezone

from app.config import get_settings
from app.services.weather import aggregate_daily, aggregate_mid_daily, latest_base_datetime, latest_mid_base_datetime


def test_latest_forecast_base_waits_for_kma_publication():
    kst = timezone(timedelta(hours=9))
    assert latest_base_datetime(datetime(2026, 7, 15, 11, 9, tzinfo=kst)).strftime("%Y%m%d%H%M") == "202607150800"
    assert latest_base_datetime(datetime(2026, 7, 15, 0, 5, tzinfo=kst)).strftime("%Y%m%d%H%M") == "202607142300"
    assert latest_mid_base_datetime(datetime(2026, 7, 15, 18, 9, tzinfo=kst)).strftime("%Y%m%d%H%M") == "202607150600"
    assert latest_mid_base_datetime(datetime(2026, 7, 15, 18, 15, tzinfo=kst)).strftime("%Y%m%d%H%M") == "202607151800"


def test_aggregate_daily_forecast():
    items = [
        {"fcstDate": "20260715", "fcstTime": "0600", "category": "TMP", "fcstValue": "21"},
        {"fcstDate": "20260715", "fcstTime": "1500", "category": "TMP", "fcstValue": "29"},
        {"fcstDate": "20260715", "fcstTime": "1200", "category": "SKY", "fcstValue": "3"},
        {"fcstDate": "20260715", "fcstTime": "1200", "category": "PTY", "fcstValue": "0"},
        {"fcstDate": "20260715", "fcstTime": "0900", "category": "POP", "fcstValue": "20"},
        {"fcstDate": "20260715", "fcstTime": "1500", "category": "POP", "fcstValue": "40"},
        {"fcstDate": "20260715", "fcstTime": "1200", "category": "REH", "fcstValue": "65"},
        {"fcstDate": "20260715", "fcstTime": "1200", "category": "WSD", "fcstValue": "3.4"},
    ]
    result = aggregate_daily(items, date(2026, 7, 15), date(2026, 7, 16))
    assert len(result) == 1
    assert result[0].condition == "구름 많음"
    assert result[0].temperature_min == 21
    assert result[0].temperature_max == 29
    assert result[0].precipitation_probability == 40
    assert result[0].humidity == 65
    assert result[0].wind_speed == 3.4


def test_aggregate_mid_forecast_combines_land_and_seoul_temperature():
    land = {
        "wf3Am": "구름많음", "wf3Pm": "흐리고 비",
        "rnSt3Am": 30, "rnSt3Pm": 70,
        "wf8": "맑음", "rnSt8": 10,
    }
    temperature = {"taMin3": 22, "taMax3": 29, "taMin8": 20, "taMax8": 28}
    result = aggregate_mid_daily(land, temperature, date(2026, 7, 15), date(2026, 7, 18), date(2026, 7, 23))
    assert len(result) == 2
    assert result[0].date == date(2026, 7, 18)
    assert result[0].forecast_type == "mid"
    assert result[0].condition == "구름많음 / 흐리고 비"
    assert result[0].precipitation_probability == 70
    assert result[0].temperature_min == 22
    assert result[1].date == date(2026, 7, 23)


def test_weather_endpoint_validates_dates_and_key(client, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "kma_service_key", "")
    monkeypatch.setattr(settings, "kma_short_service_key", "")
    monkeypatch.setattr(settings, "kma_mid_service_key", "")
    too_long = client.get("/api/weather/seoul", params={"start_date": "2026-07-15", "end_date": "2026-07-25"})
    assert too_long.status_code == 400
    no_key = client.get("/api/weather/seoul", params={"start_date": "2026-07-15", "end_date": "2026-07-24"})
    assert no_key.status_code == 503
    assert "API 키" in no_key.json()["detail"]
