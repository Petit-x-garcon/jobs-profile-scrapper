"""Schemas shared between the scraper and its callers."""

from datetime import datetime

from pydantic import BaseModel


class JobIn(BaseModel):
    """A scraped job posting. `url` is the dedupe key."""

    source: str
    url: str
    title: str
    company: str | None = None
    location: str | None = None
    description: str
    posted_at: datetime | None = None
