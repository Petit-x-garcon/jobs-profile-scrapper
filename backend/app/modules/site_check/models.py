import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ScrapeSite(Base):
    """A checked URL included in future scrape runs."""

    __tablename__ = "scrape_sites"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    url: Mapped[str] = mapped_column(String(2048), unique=True)


class CrawlRun(Base):
    """Persistent progress for an interactive Site Check crawl."""

    __tablename__ = "site_crawls"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    url: Mapped[str] = mapped_column(String(2048))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    status: Mapped[str] = mapped_column(String(16), default="queued")
    current_url: Mapped[str | None] = mapped_column(String(2048))
    checked: Mapped[int] = mapped_column(default=0)
    discovered: Mapped[int] = mapped_column(default=1)
    job_count: Mapped[int] = mapped_column(default=0)
    error: Mapped[str | None] = mapped_column(String(500))


class CrawlPage(Base):
    """One completed page, ordered by its checkpoint in the crawl."""

    __tablename__ = "site_crawl_pages"

    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("site_crawls.id"), primary_key=True)
    position: Mapped[int] = mapped_column(primary_key=True)
    result: Mapped[dict] = mapped_column(JSON)
