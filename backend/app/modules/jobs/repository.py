import re
import uuid

from sqlalchemy import Select, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.jobs.models import Job
from app.modules.jobs.schemas import JobQuery
from app.shared.pagination import paginate

_SEARCHED = (Job.title, Job.company, Job.location, Job.description)


async def upsert_many(jobs: list[dict], db: AsyncSession) -> int:
    """Insert jobs whose url is not stored yet; return how many were added."""
    urls = {j["url"] for j in jobs}
    existing = set(await db.scalars(select(Job.url).where(Job.url.in_(urls))))
    new = {j["url"]: Job(**j) for j in jobs if j["url"] not in existing}  # dedupes within batch
    db.add_all(new.values())
    await db.commit()
    return len(new)


async def add(job: dict, db: AsyncSession) -> Job:
    """Insert a single job."""
    obj = Job(**job)
    db.add(obj)
    await db.commit()
    return obj


async def get(job_id: uuid.UUID, db: AsyncSession) -> Job | None:
    """Fetch one job by id."""
    return await db.get(Job, job_id)


async def get_many(job_ids: list[uuid.UUID], db: AsyncSession) -> list[Job]:
    """Fetch the jobs with these ids (missing ids are skipped)."""
    return list(await db.scalars(select(Job).where(Job.id.in_(job_ids))))


def _word_pattern(keyword: str) -> str:
    """Case-insensitive whole-word regex: "AI" matches "AI engineer", not "maintain".

    Plain character classes instead of \\b or \\m, so the pattern works in both
    Postgres and SQLite (tests).
    """
    return f"(^|[^a-z0-9]){re.escape(keyword.lower())}([^a-z0-9]|$)"


async def list_jobs(
    filters: JobQuery, page: int, size: int, db: AsyncSession
) -> tuple[list[Job], int]:
    """Filtered page of jobs: best score first (nulls last), then newest."""
    stmt: Select = select(Job)
    if filters.source:
        stmt = stmt.where(Job.source == filters.source)
    if filters.min_score is not None:
        stmt = stmt.where(Job.score >= filters.min_score)
    for keyword in filters.keywords:
        pattern = _word_pattern(keyword)
        stmt = stmt.where(or_(*(func.lower(col).regexp_match(pattern) for col in _SEARCHED)))
    stmt = stmt.order_by(Job.score.desc().nulls_last(), Job.scraped_at.desc())
    return await paginate(db, stmt, page, size)


async def reset_scores(db: AsyncSession) -> None:
    """Clear AI match data on every job (summary is kept). The caller commits."""
    await db.execute(
        update(Job).values(score=None, match_reason=None, matching_skills=None, missing_skills=None)
    )
