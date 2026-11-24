import uuid

from pydantic import BaseModel, Field

from app.modules.jobs.schemas import JobOut

MAX_JOBS = 20


class AnalyzeIn(BaseModel):
    """Jobs to analyze against the current profile (usually the page the user sees)."""

    job_ids: list[uuid.UUID] = Field(min_length=1, max_length=MAX_JOBS)


class RecommendationsOut(BaseModel):
    """Analyzed jobs ranked by match score, best first."""

    items: list[JobOut]
    analyzed: int  # new AI calls made; the rest came from earlier analysis
    failed: int
