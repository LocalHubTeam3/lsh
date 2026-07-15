import re

from openai import AsyncOpenAI
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Course, Location, Post
from app.schemas.chat import ChatRequest, ChatResponse, Reference
from app.services.llm import generate_text


# 초기 동작용 프롬프트입니다. 이후 챗봇 프롬프트는 이 값만 교체할 수 있습니다.
CHAT_INSTRUCTIONS = (
    "당신은 LocalHub 서울 여행 도우미입니다. localhub_search_results에 있는 사실만 근거로 답하세요. "
    "검색 결과가 부족하면 부족하다고 명확히 말하고, 제공되지 않은 장소나 사실을 만들어내지 마세요. "
    "민감정보를 요구하거나 출력하지 말고 한국어로 간결하게 답하세요."
)


def _patterns(message: str) -> list[str]:
    terms = [message.strip(), *re.findall(r"[가-힣A-Za-z0-9]{2,}", message)]
    return [f"%{term}%" for term in dict.fromkeys(terms) if term]


def _context(db: Session, message: str) -> tuple[list[dict[str, object]], list[Reference]]:
    patterns = _patterns(message)
    location_filters = [or_(Location.title.ilike(p), Location.address.ilike(p)) for p in patterns]
    course_filters = [or_(Course.title.ilike(p), Course.description.ilike(p)) for p in patterns]
    post_filters = [or_(Post.title.ilike(p), Post.content.ilike(p)) for p in patterns]
    locations = db.scalars(select(Location).where(or_(*location_filters)).limit(5)).all() if patterns else []
    courses = db.scalars(select(Course).where(or_(*course_filters)).limit(5)).all() if patterns else []
    posts = db.scalars(select(Post).where(or_(*post_filters)).limit(5)).all() if patterns else []
    context: list[dict[str, object]] = []
    references: list[Reference] = []
    for item in locations:
        context.append({"type": "location", "id": item.id, "title": item.title, "address": item.address, "category": item.category3 or item.category2 or item.category1})
        references.append(Reference(type="location", id=item.id, title=item.title))
    for item in courses:
        context.append({"type": "course", "id": item.id, "title": item.title, "description": item.description, "views": item.views})
        references.append(Reference(type="course", id=item.id, title=item.title))
    for item in posts:
        context.append({"type": "post", "id": item.id, "title": item.title, "category": item.category, "content": item.content, "views": item.views})
        references.append(Reference(type="post", id=item.id, title=item.title))
    return context, references


async def answer(db: Session, request: ChatRequest) -> ChatResponse:
    context, references = _context(db, request.message)
    history = request.history[-6:]
    result = await generate_text(
        instructions=CHAT_INSTRUCTIONS,
        payload={
            "history": [item.model_dump() for item in history],
            "question": request.message,
            "localhub_search_results": context,
        },
        client_factory=AsyncOpenAI,
    )
    return ChatResponse(answer=result, references=references)
