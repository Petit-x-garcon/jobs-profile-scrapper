import re
import uuid
from collections.abc import AsyncIterator

from sqlalchemy import Select, func, or_, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.jobs.models import Job
from app.modules.jobs.schemas import JobQuery
from app.shared.pagination import paginate

_SEARCHED = (Job.title, Job.company, Job.location, Job.description)


async def upsert_many(jobs: list[dict], db: AsyncSession) -> int:
    """Insert jobs whose url is not stored yet; return how many were added."""
    if not jobs:
        return 0
    insert = sqlite_insert if db.get_bind().dialect.name == "sqlite" else pg_insert
    stmt = insert(Job).on_conflict_do_nothing(index_elements=[Job.url]).returning(Job.id)
    inserted = (await db.scalars(stmt, jobs)).all()
    await db.commit()
    return len(inserted)


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


def _filtered_jobs(filters: JobQuery) -> Select:
    stmt: Select = select(Job)
    if filters.source:
        stmt = stmt.where(Job.source == filters.source)
    if filters.min_score is not None:
        stmt = stmt.where(Job.score >= filters.min_score)
    for keyword in filters.keywords:
        pattern = _word_pattern(keyword)
        stmt = stmt.where(or_(*(func.lower(col).regexp_match(pattern) for col in _SEARCHED)))
    return stmt.order_by(Job.scraped_at.desc(), Job.id.desc())


async def iter_filtered_jobs(filters: JobQuery, db: AsyncSession) -> AsyncIterator[Job]:
    """Stream filtered jobs newest first for the local shortlist."""
    rows = await db.stream_scalars(_filtered_jobs(filters).execution_options(yield_per=200))
    try:
        async for job in rows:
            yield job
    finally:
        await rows.close()


async def list_jobs(
    filters: JobQuery, page: int, size: int, db: AsyncSession
) -> tuple[list[Job], int]:
    """Filtered page of jobs: most recently saved first."""
    return await paginate(db, _filtered_jobs(filters), page, size)


async def reset_scores(db: AsyncSession) -> None:
    """Clear AI match data on every job (summary is kept). The caller commits."""
    await db.execute(
        update(Job).values(score=None, match_reason=None, matching_skills=None, missing_skills=None)
    )
