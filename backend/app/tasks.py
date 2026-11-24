import asyncio
import logging

from app.celery_app import celery_app
from app.core.database import task_session
from app.modules.jobs import service as jobs_service

logger = logging.getLogger(__name__)


async def _scrape_jobs(query: str) -> None:
    from app.modules.scraper.service import scrape  # lazy: module owned elsewhere
    from app.modules.site_check.service import list_source_urls, scrape_source

    async with task_session() as db:
        urls = await list_source_urls(db)
    scraped = await scrape(query)
    for url in urls:
        try:
            job = await asyncio.wait_for(scrape_source(url), timeout=60)
        except Exception as exc:
            logger.warning("Failed to scrape a saved source (%s)", type(exc).__name__)
            continue
        if job is not None:
            scraped.append(job)
    async with task_session() as db:
        added = await jobs_service.save_scraped([j.model_dump() for j in scraped], db)
    logger.info("Scraped %d, added %d", len(scraped), added)


@celery_app.task
def scrape_jobs(query: str) -> None:
    """Scrape all sources and store new jobs. AI analysis runs only when the user asks."""
    asyncio.run(_scrape_jobs(query))
