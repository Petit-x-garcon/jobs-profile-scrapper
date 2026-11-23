import asyncio
import logging

from app.celery_app import celery_app
from app.core.database import task_session
from app.modules.jobs import service as jobs_service

logger = logging.getLogger(__name__)


async def _scrape_and_enrich(query: str) -> None:
    from app.modules.scraper.service import scrape  # lazy: module owned elsewhere

    scraped = await scrape(query)
    async with task_session() as db:
        added = await jobs_service.save_scraped([j.model_dump() for j in scraped], db)
        enriched = await jobs_service.enrich_pending(db)
    logger.info("Scraped %d, added %d, enriched %d", len(scraped), added, enriched)


async def _enrich_pending() -> None:
    async with task_session() as db:
        enriched = await jobs_service.enrich_pending(db)
    logger.info("Enriched %d jobs", enriched)


@celery_app.task
def scrape_and_enrich(query: str) -> None:
    """Scrape, store new jobs, then enrich only un-enriched ones."""
    asyncio.run(_scrape_and_enrich(query))


@celery_app.task
def enrich_pending() -> None:
    """Enrich jobs that lack a summary or score."""
    asyncio.run(_enrich_pending())
