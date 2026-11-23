import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


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
    scraped_at: datetime


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
