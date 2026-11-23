import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai import service as ai
from app.modules.jobs import repository
from app.modules.jobs.models import Job
from app.modules.jobs.schemas import ImportIn
from app.modules.profile import service as profile_service
from app.shared.exceptions import NotFound

logger = logging.getLogger(__name__)


def _enqueue_enrich() -> None:
    """Queue enrichment of pending jobs; a broker outage must not fail the request."""
    try:
        from app.tasks import enrich_pending  # lazy: tasks import this module

        enrich_pending.delay()
    except Exception:
        logger.exception("Could not enqueue enrichment")


def enqueue_scrape(query: str) -> str:
    """Queue a scrape-and-enrich run and return the Celery task id."""
    from app.tasks import scrape_and_enrich

    return scrape_and_enrich.delay(query).id


async def get_job(job_id: uuid.UUID, db: AsyncSession) -> Job:
    """Return a job or raise NotFound."""
    job = await repository.get(job_id, db)
    if job is None:
        raise NotFound("Job not found.")
    return job


async def import_job(data: ImportIn, db: AsyncSession) -> Job:
    """Store a manually pasted job and queue enrichment."""
    first_line = data.text.strip().splitlines()[0][:200] if data.text.strip() else "Untitled"
    job = await repository.add(
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
    _enqueue_enrich()
    return job


async def save_scraped(jobs: list[dict], db: AsyncSession) -> int:
    """Store scraped jobs, skipping urls already present."""
    return await repository.upsert_many(jobs, db)


async def reset_and_rescore(db: AsyncSession) -> None:
    """Drop all scores (profile changed) and queue re-scoring."""
    await repository.reset_scores(db)
    _enqueue_enrich()


async def enrich_pending(db: AsyncSession) -> int:
    """Enrich only jobs missing summary or score; return how many were updated."""
    pending = await repository.list_unenriched(db)
    if not pending:
        return 0
    profile_text = profile_service.profile_text(await profile_service.get_profile(db))
    done = 0
    for job in pending:
        try:
            result = await ai.enrich(f"{job.title}\n{job.description}", profile_text)
        except ai.AIUnavailable:
            logger.info("AI not configured; skipping enrichment")
            break
        except Exception:
            logger.exception("Enrichment failed for job %s", job.id)
            continue
        job.summary = job.summary or result.summary
        job.score = result.score
        job.match_reason = result.reasons
        await db.commit()
        done += 1
    return done
