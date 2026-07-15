from pydantic import BaseModel, ConfigDict


class LocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    content_id: str
    title: str
    address: str | None
    address_detail: str | None
    longitude: float | None
    latitude: float | None
    image_url: str | None
    description: str | None
    content_type_id: str | None
    category1: str | None
    category2: str | None
    category3: str | None


class LocationList(BaseModel):
    items: list[LocationOut]
    page: int
    size: int
    total: int
