import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Profile(Base):
    """The single user profile row."""

    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    headline: Mapped[str] = mapped_column(String(300))
    skills: Mapped[list[str]] = mapped_column(JSON)
    years_experience: Mapped[int] = mapped_column(Integer)
    locations: Mapped[list[str]] = mapped_column(JSON)
    remote_ok: Mapped[bool]
    min_salary: Mapped[int | None] = mapped_column(Integer)
    summary: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
