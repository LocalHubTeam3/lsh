from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(primary_key=True)
    content_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(300), index=True)
    address: Mapped[str | None] = mapped_column(String(500))
    address_detail: Mapped[str | None] = mapped_column(String(300))
    longitude: Mapped[float | None] = mapped_column(Float)
    latitude: Mapped[float | None] = mapped_column(Float)
    image_url: Mapped[str | None] = mapped_column(String(1000))
    description: Mapped[str | None] = mapped_column(Text)
    content_type_id: Mapped[str | None] = mapped_column(String(20), index=True)
    category1: Mapped[str | None] = mapped_column(String(50), index=True)
    category2: Mapped[str | None] = mapped_column(String(50), index=True)
    category3: Mapped[str | None] = mapped_column(String(50), index=True)
    crowd_area_code: Mapped[str | None] = mapped_column(String(50), index=True)
    crowd_area_name: Mapped[str | None] = mapped_column(String(200))
    posts: Mapped[list["Post"]] = relationship(back_populates="location")


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Post(TimestampMixin, Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(50), index=True)
    nickname: Mapped[str] = mapped_column(String(30), default="익명", server_default="익명", index=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    content: Mapped[str] = mapped_column(Text)
    edit_password: Mapped[str] = mapped_column(String(100))
    views: Mapped[int] = mapped_column(Integer, default=0)
    location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"), index=True)
    location: Mapped[Location | None] = relationship(back_populates="posts")


class Course(TimestampMixin, Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str] = mapped_column(Text)
    edit_password: Mapped[str] = mapped_column(String(100))
    views: Mapped[int] = mapped_column(Integer, default=0)
    places: Mapped[list["CoursePlace"]] = relationship(
        back_populates="course", cascade="all, delete-orphan", order_by="CoursePlace.sequence"
    )


class CoursePlace(Base):
    __tablename__ = "course_places"
    __table_args__ = (UniqueConstraint("course_id", "sequence"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), index=True)
    sequence: Mapped[int] = mapped_column(Integer)
    course: Mapped[Course] = relationship(back_populates="places")
    location: Mapped[Location] = relationship()


class CrowdCache(Base):
    __tablename__ = "crowd_cache"

    area_code: Mapped[str] = mapped_column(String(50), primary_key=True)
    area_name: Mapped[str] = mapped_column(String(200))
    congestion_level: Mapped[str | None] = mapped_column(String(50))
    population_min: Mapped[int | None] = mapped_column(Integer)
    population_max: Mapped[int | None] = mapped_column(Integer)
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cached_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
