from datetime import date, datetime

from typing import Literal

from pydantic import BaseModel


class DailyWeather(BaseModel):
    date: date
    forecast_type: Literal["short", "mid"] = "short"
    condition: str
    temperature_min: float | None = None
    temperature_max: float | None = None
    precipitation_probability: int | None = None
    humidity: int | None = None
    wind_speed: float | None = None


class WeatherForecast(BaseModel):
    location: str
    base_datetime: datetime
    items: list[DailyWeather]
