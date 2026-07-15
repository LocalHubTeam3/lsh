from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


def _ensure_sqlite_directory(url: str) -> None:
    prefix = "sqlite:///"
    if url.startswith(prefix) and url != "sqlite:///:memory:":
        Path(url.removeprefix(prefix)).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)


settings = get_settings()
_ensure_sqlite_directory(settings.database_url)
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    if engine.dialect.name == "sqlite":
        columns = {item["name"] for item in inspect(engine).get_columns("locations")}
        post_columns = {item["name"] for item in inspect(engine).get_columns("posts")}
        with engine.begin() as connection:
            if "description" not in columns:
                connection.exec_driver_sql("ALTER TABLE locations ADD COLUMN description TEXT")
            if "location_id" not in post_columns:
                connection.exec_driver_sql("ALTER TABLE posts ADD COLUMN location_id INTEGER REFERENCES locations(id)")
                connection.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_posts_location_id ON posts (location_id)")
