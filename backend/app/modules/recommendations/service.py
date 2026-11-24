import asyncio
import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai import service as ai
from app.modules.ai.schemas import Enrichment
from app.modules.jobs import service as jobs_service
from app.modules.jobs.schemas import JobOut
from app.modules.profile import service as profile_service
from app.modules.recommendations.schemas import RecommendationsOut
from app.shared.exceptions import NotFound

logger = logging.getLogger(__name__)

AI_CONCURRENCY = 5


async def _score_all(job_texts: list[str], profile_text: str) -> list[Enrichment | BaseException]:
    """Run the AI calls concurrently (bounded); no DB access in here."""
    gate = asyncio.Semaphore(AI_CONCURRENCY)

    async def one(text: str) -> Enrichment:
        async with gate:
            return await ai.enrich(text, profile_text)

    return await asyncio.gather(*(one(t) for t in job_texts), return_exceptions=True)


async def analyze(job_ids: list[uuid.UUID], db: AsyncSession) -> RecommendationsOut:
    """Score jobs against the latest profile and rank them.

    Jobs scored since the last profile/CV change are reused, so only new ones cost an
    AI call. Raises AIUnavailable when AI is not configured, NotFound if no job exists.
    """
    jobs = await jobs_service.get_jobs(job_ids, db)
    if not jobs:
        raise NotFound("None of these jobs exist. Refresh the list and try again.")
    pending = [j for j in jobs if j.score is None]
    failed = 0
    if pending:
        profile_text = profile_service.profile_text(await profile_service.get_profile(db))
        results = await _score_all([f"{j.title}\n{j.description}" for j in pending], profile_text)
        for job, result in zip(pending, results, strict=True):
            if isinstance(result, ai.AIUnavailable):
                raise result
            if isinstance(result, BaseException):
                logger.error("Analysis failed for job %s", job.id, exc_info=result)
                failed += 1
                continue
            jobs_service.apply_analysis(job, result)
        await db.commit()
    ranked = sorted((j for j in jobs if j.score is not None), key=lambda j: -(j.score or 0))
    return RecommendationsOut(
        items=[JobOut.model_validate(j) for j in ranked],
        analyzed=len(pending) - failed,
        failed=failed,
    )
