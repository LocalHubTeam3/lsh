from pydantic import BaseModel, ConfigDict


class MapLocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    content_id: str
    title: str
    address: str | None
    latitude: float
    longitude: float
    image_url: str | None
    content_type_id: str


class MapLocationList(BaseModel):
    items: list[MapLocationOut]
    total: int
    content_type: str


class MapSearchList(BaseModel):
    items: list[MapLocationOut]
    total: int
    query: str
