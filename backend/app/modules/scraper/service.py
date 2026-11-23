"""Run every job-site adapter and combine the results."""

import asyncio
import logging

import httpx

from app.modules.scraper.adapters import dodojob, jobify
from app.modules.scraper.adapters._common import USER_AGENT
from app.modules.scraper.schemas import JobIn

logger = logging.getLogger(__name__)


async def scrape(query: str, max_jobs_per_source: int = 30) -> list[JobIn]:
    """Scrape all sources; a failing adapter is logged and skipped. Deduped by url."""
    adapters = {
        "dodojob": dodojob.fetch,
        "jobify": jobify.fetch,
    }  # looked up at call time
    async with httpx.AsyncClient(
        timeout=20, follow_redirects=True, headers={"User-Agent": USER_AGENT}
    ) as client:
        results = await asyncio.gather(
            *(fetch(client, query, max_jobs_per_source) for fetch in adapters.values()),
            return_exceptions=True,
        )
    jobs: dict[str, JobIn] = {}
    for name, result in zip(adapters, results, strict=True):
        if isinstance(result, BaseException):
            logger.error("adapter %s failed", name, exc_info=result)
            continue
        for job in result:
            jobs.setdefault(job.url, job)
    return list(jobs.values())
