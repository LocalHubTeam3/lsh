from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = f"sqlite:///{(BASE_DIR / 'data' / 'localhub.db').as_posix()}"
    frontend_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    openai_api_key: str = ""
    openai_model: str = "gpt-5-mini"
    seoul_api_key: str = ""
    kma_service_key: str = ""
    kma_short_service_key: str = ""
    kma_mid_service_key: str = ""
    external_api_timeout: float = 10.0
    openai_timeout: float = 45.0

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

    @field_validator("frontend_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: object) -> object:
        if isinstance(value, str) and not value.lstrip().startswith("["):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
