from typing import Literal

from pydantic import BaseModel, Field


class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    history: list[HistoryMessage] = Field(default_factory=list, max_length=20)


class Reference(BaseModel):
    type: Literal["location", "course", "post"]
    id: int
    title: str


class ChatResponse(BaseModel):
    answer: str
    references: list[Reference]
