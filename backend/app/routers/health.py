from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/features")
def feature_status() -> dict[str, bool]:
    settings = get_settings()
    return {
        "openai_api_configured": bool(settings.openai_api_key),
        "seoul_api_configured": bool(settings.seoul_api_key),
    }
