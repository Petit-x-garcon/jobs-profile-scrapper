from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

RobotsStatus = Literal["allowed", "disallowed", "not_found", "unavailable"]
CheckResult = Literal["successful", "failed", "restricted", "inconclusive"]


class SiteCheckIn(BaseModel):
    """URL to test."""

    url: str = Field(min_length=1, max_length=2048)


class SiteCheckOut(BaseModel):
    """Outcome of a scraping test.

    `robots_status` is about permission (not_found = no robots.txt, so no restriction);
    `http_status` is about technical access. `message` explains the result.
    """

    url: str
    final_url: str | None = None
    http_status: int | None = None
    robots_status: RobotsStatus
    result: CheckResult
    message: str
    content_preview: str | None = None


class ScrapeSiteOut(BaseModel):
    """A URL saved as a scrape source."""

    id: UUID
    url: str
