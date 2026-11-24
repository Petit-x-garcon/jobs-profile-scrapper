from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

RobotsStatus = Literal["allowed", "disallowed", "not_found", "unavailable"]
CheckResult = Literal["successful", "failed", "restricted", "inconclusive"]


class SiteCheckIn(BaseModel):
    """URL to test."""

    url: str = Field(min_length=1, max_length=2048)
    origin: str | None = Field(default=None, max_length=2048)


class CrawlJob(BaseModel):
    """The job fields kept from a crawl, with the source URL for duplicate detection."""

    model_config = ConfigDict(str_strip_whitespace=True, from_attributes=True)
    url: str = Field(max_length=2048)
    title: str = Field(min_length=1, max_length=500)
    description: str = Field(min_length=1)

    @field_validator("url")
    @classmethod
    def validate_web_url(cls, value: str) -> str:
        """Require an HTTP(S) URL and preserve its original deduplication key."""
        HttpUrl(value)
        return value


class CrawlImportIn(BaseModel):
    """A batch of filtered crawl results."""

    jobs: list[CrawlJob] = Field(max_length=100)


class CrawlImportOut(BaseModel):
    """Number of new and previously stored postings in an import."""

    added: int
    skipped: int


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
    job_count: int | None = None
    content_text: str | None = None
    job_tabs: dict[str, list[str]] = Field(default_factory=dict)
    jobs: list[CrawlJob] = Field(default_factory=list)
    job_urls: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)


class ScrapeSiteOut(BaseModel):
    """A URL saved as a scrape source."""

    id: UUID
    url: str


class CrawlStatus(BaseModel):
    """Status shown while the background worker follows discovered links."""

    model_config = ConfigDict(from_attributes=True)
    id: UUID
    url: str
    status: Literal["queued", "running", "completed", "stopped", "failed"]
    current_url: str | None
    discovered: int
    checked: int
    job_count: int
    error: str | None
