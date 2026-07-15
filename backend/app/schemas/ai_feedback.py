from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class BasketWeatherItem(BaseModel):
    date: date
    forecast_type: Literal["short", "mid"] | None = None
    condition: str = Field(min_length=1, max_length=100)
    temperature_min: float | None = None
    temperature_max: float | None = None
    precipitation_probability: int | None = Field(default=None, ge=0, le=100)
    humidity: int | None = Field(default=None, ge=0, le=100)
    wind_speed: float | None = Field(default=None, ge=0)


class TravelBasketFeedbackRequest(BaseModel):
    location_ids: list[int] = Field(min_length=1, max_length=20)
    request: str | None = Field(default=None, min_length=1, max_length=2000)
    weather: list[BasketWeatherItem] = Field(default_factory=list, max_length=10)


class BasketLocationReference(BaseModel):
    id: int
    title: str


class RouteLeg(BaseModel):
    from_id: int
    from_title: str
    to_id: int
    to_title: str
    distance_km: float


class RouteAnalysis(BaseModel):
    location_ids: list[int]
    total_distance_km: float
    legs: list[RouteLeg]


class TravelBasketFeedbackResponse(BaseModel):
    feedback: str
    references: list[BasketLocationReference]
    current_route: RouteAnalysis
    recommended_route: RouteAnalysis
    distance_saved_km: float
