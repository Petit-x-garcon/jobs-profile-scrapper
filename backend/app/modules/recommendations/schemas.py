import uuid

from pydantic import BaseModel, Field

from app.modules.jobs.schemas import JobOut, JobQuery

MAX_JOBS = 20


class AnalyzeIn(BaseModel):
    """Jobs to analyze against the current profile."""

    job_ids: list[uuid.UUID] = Field(min_length=1, max_length=MAX_JOBS)


class RecommendationsOut(BaseModel):
    """Analyzed jobs ranked by match score, best first."""

    items: list[JobOut]
    analyzed: int  # new AI calls made; the rest came from earlier analysis
    failed: int


class RankingQuery(JobQuery):
    """Jobs page filters and a one-based ranking page."""

    page: int = Field(default=1, ge=1)


class LocalMatch(BaseModel):
    """A globally ranked job with its local matching evidence."""

    rank: int
    job: JobOut
    role_match: bool
    matching_skills: list[str]


class ShortlistQuery(JobQuery):
    """Older preview clients omit the page; paginated clients supply it."""

    page: int | None = Field(default=None, ge=1)


class ShortlistItem(BaseModel):
    """Flat match returned to the original preview panel."""

    id: uuid.UUID
    title: str
    company: str | None
    role_match: bool
    matching_skills: list[str]
    analyzed: bool
