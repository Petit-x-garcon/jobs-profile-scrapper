import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.schemas import Enrichment
from app.modules.jobs import repository
from app.modules.jobs.models import Job
from app.modules.jobs.schemas import ImportIn
from app.shared.exceptions import NotFound


def enqueue_scrape(query: str) -> str:
    """Queue a scrape run and return the Celery task id."""
    from app.tasks import scrape_jobs  # lazy: tasks import this module

    return scrape_jobs.delay(query).id


async def get_job(job_id: uuid.UUID, db: AsyncSession) -> Job:
    """Return a job or raise NotFound."""
    job = await repository.get(job_id, db)
    if job is None:
        raise NotFound("Job not found.")
    return job


async def get_jobs(job_ids: list[uuid.UUID], db: AsyncSession) -> list[Job]:
    """Return the jobs with these ids; unknown ids are ignored."""
    return await repository.get_many(job_ids, db)


async def import_job(data: ImportIn, db: AsyncSession) -> Job:
    """Store a manually pasted job (no AI; analysis is on request)."""
    first_line = data.text.strip().splitlines()[0][:200] if data.text.strip() else "Untitled"
    return await repository.add(
        {
            "source": "manual",
            "url": data.url or f"manual:{uuid.uuid4()}",
            "title": data.title or first_line,
            "company": None,
            "location": None,
            "description": data.text,
            "posted_at": None,
        },
        db,
    )


async def save_scraped(jobs: list[dict], db: AsyncSession) -> int:
    """Store scraped jobs, skipping urls already present."""
    return await repository.upsert_many(jobs, db)


def apply_analysis(job: Job, result: Enrichment) -> None:
    """Copy an AI analysis onto a job. The caller commits."""
    job.summary = job.summary or result.summary
    job.score = result.score
    job.match_reason = result.reasons
    job.matching_skills = result.matching_skills
    job.missing_skills = result.missing_skills


async def reset_scores(db: AsyncSession) -> None:
    """Drop all AI match data because the profile changed. The caller commits."""
    await repository.reset_scores(db)
