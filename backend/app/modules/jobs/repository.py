import uuid

from sqlalchemy import Select, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.jobs.models import Job
from app.shared.pagination import paginate


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


async def list_jobs(
    page: int, size: int, source: str | None, min_score: int | None, db: AsyncSession
) -> tuple[list[Job], int]:
    """Filtered page of jobs: best score first (nulls last), then newest."""
    stmt: Select = select(Job)
    if source:
        stmt = stmt.where(Job.source == source)
    if min_score is not None:
        stmt = stmt.where(Job.score >= min_score)
    stmt = stmt.order_by(Job.score.desc().nulls_last(), Job.scraped_at.desc())
    return await paginate(db, stmt, page, size)


async def list_unenriched(db: AsyncSession) -> list[Job]:
    """Jobs missing a summary or a score."""
    stmt = select(Job).where(or_(Job.summary.is_(None), Job.score.is_(None)))
    return list(await db.scalars(stmt))


async def reset_scores(db: AsyncSession) -> None:
    """Clear score and match_reason on every job (summary is kept)."""
    await db.execute(update(Job).values(score=None, match_reason=None))
    await db.commit()
