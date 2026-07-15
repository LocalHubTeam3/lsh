from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.routers import ai_feedback, chat, courses, health, locations, map_locations, posts, weather


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="LocalHub API", version="1.0.0", lifespan=lifespan)
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health.router)
app.include_router(locations.router)
app.include_router(map_locations.router)
app.include_router(posts.router)
app.include_router(courses.router)
app.include_router(chat.router)
app.include_router(ai_feedback.router)
app.include_router(weather.router)


@app.get("/", include_in_schema=False)
def api_root() -> dict[str, str]:
    return {"service": "LocalHub API", "docs": "/docs", "health": "/api/health"}
