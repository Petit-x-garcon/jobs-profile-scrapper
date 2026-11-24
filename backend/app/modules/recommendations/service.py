import asyncio
import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai import service as ai
from app.modules.ai.schemas import Enrichment
from app.modules.jobs import service as jobs_service
from app.modules.jobs.schemas import JobOut
from app.modules.profile import service as profile_service
from app.modules.recommendations.matching import RoleMatcher, skill_patterns
from app.modules.recommendations.schemas import (
    LocalMatch,
    RankingQuery,
    RecommendationsOut,
    ShortlistItem,
    ShortlistQuery,
)
from app.shared.exceptions import NotFound
from app.shared.pagination import Page

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


async def shortlist(filters: RankingQuery, db: AsyncSession) -> Page[LocalMatch]:
    """Prefer role matches, then distinct skills; stable ties keep the newest jobs first."""
    profile = await profile_service.get_profile(db)
    roles = RoleMatcher(profile.headline, profile.experience)
    skills = skill_patterns(profile.skills)
    ranked: list[tuple[uuid.UUID, bool, list[str]]] = []
    async for job in jobs_service.iter_filtered_jobs(filters, db):
        role = roles.matches(job.title)
        text = f"{job.title}\n{job.description}"
        matched = [skill for skill, pattern in skills if pattern.search(text)]
        ranked.append((job.id, role, matched))
    ranked.sort(key=lambda row: (row[1], len(row[2])), reverse=True)
    size = 10
    offset = (filters.page - 1) * size
    visible = ranked[offset : offset + size]
    jobs = {job.id: job for job in await jobs_service.get_jobs([row[0] for row in visible], db)}
    items = [
        LocalMatch(
            rank=rank,
            job=JobOut.model_validate(jobs[job_id]),
            role_match=role,
            matching_skills=matched,
        )
        for rank, (job_id, role, matched) in enumerate(visible, start=offset + 1)
        if job_id in jobs
    ]
    return Page(items=items, page=filters.page, size=size, total=len(ranked))


async def legacy_shortlist(
    filters: ShortlistQuery, db: AsyncSession
) -> list[ShortlistItem] | Page[LocalMatch]:
    """Serve the original ten-item preview or an explicitly requested ranking page."""
    query = RankingQuery(**filters.model_dump(exclude={"page"}), page=filters.page or 1)
    ranked = await shortlist(query, db)
    if filters.page is not None:
        return ranked
    return [
        ShortlistItem(
            id=row.job.id,
            title=row.job.title,
            company=row.job.company,
            role_match=row.role_match,
            matching_skills=row.matching_skills,
            analyzed=row.job.score is not None,
        )
        for row in ranked.items
        if row.role_match or row.matching_skills
    ]
