import asyncio
import logging

from app.celery_app import celery_app
from app.core.database import task_session
from app.modules.jobs import service as jobs_service

logger = logging.getLogger(__name__)


async def _scrape_jobs(query: str) -> None:
    from app.modules.scraper.service import scrape  # lazy: module owned elsewhere
    from app.modules.site_check.schemas import CrawlJob
    from app.modules.site_check.service import import_crawl_jobs, list_source_urls, scrape_source

    async with task_session() as db:
        urls = await list_source_urls(db)
    scraped = await scrape(query)
    async with task_session() as db:
        added = await jobs_service.save_scraped([j.model_dump() for j in scraped], db)
    for url in urls:
        try:
            postings = await scrape_source(url)
            async with task_session() as db:
                imported = await import_crawl_jobs(
                    [CrawlJob.model_validate(j) for j in postings], db
                )
                added += imported.added
        except Exception as exc:
            logger.warning("Failed to scrape a saved source (%s)", type(exc).__name__)
            continue
    logger.info("Added %d jobs", added)


@celery_app.task
def scrape_jobs(query: str) -> None:
    """Scrape all sources and store new jobs. AI analysis runs only when the user asks."""
    asyncio.run(_scrape_jobs(query))


async def _crawl_website(run_id: str) -> None:
    from uuid import UUID

    from app.modules.site_check.service import run_background_crawl

    async with task_session() as db:
        await run_background_crawl(UUID(run_id), db)


@celery_app.task(reject_on_worker_lost=True)
def crawl_website(run_id: str) -> None:
    """Run a Site Check crawl from its last committed checkpoint."""
    asyncio.run(_crawl_website(run_id))
