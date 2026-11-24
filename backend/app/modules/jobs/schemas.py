import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class JobOut(BaseModel):
    """Job as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source: str
    url: str
    title: str
    company: str | None
    location: str | None
    description: str
    posted_at: datetime | None
    summary: str | None
    score: int | None
    match_reason: str | None
    matching_skills: list[str] | None = None
    missing_skills: list[str] | None = None
    scraped_at: datetime


class JobQuery(BaseModel):
    """List filters. `q` holds comma-separated keywords; every keyword must match."""

    source: str | None = None
    min_score: int | None = None
    q: str | None = Field(default=None, max_length=200)

    @property
    def keywords(self) -> list[str]:
        """Non-empty keywords from `q`."""
        return [k.strip() for k in (self.q or "").split(",") if k.strip()]


class ImportIn(BaseModel):
    """Manual import body."""

    url: str | None = None
    title: str | None = None
    text: str


class ScrapeIn(BaseModel):
    """Scrape request body."""

    query: str = "IT"


class TaskOut(BaseModel):
    """Enqueued task reference."""

    task_id: str
