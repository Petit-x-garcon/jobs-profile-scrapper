from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.site_check import crawl_repository, crawl_service, service
from app.modules.site_check.schemas import (
    CrawlImportIn,
    CrawlImportOut,
    CrawlStatus,
    ScrapeSiteOut,
    SiteCheckIn,
    SiteCheckOut,
)

router = APIRouter(prefix="/site-check", tags=["site-check"])


@router.post("")
async def check_site(data: SiteCheckIn) -> SiteCheckOut:
    """Test whether a website can be scraped (public, single-user app).

    400 for invalid URLs and for private/internal targets (SSRF protection).
    """
    return await service.check_site(data.url, data.origin)


@router.post("/sources", status_code=201)
async def add_source(data: SiteCheckIn, db: AsyncSession = Depends(get_db)) -> ScrapeSiteOut:
    """Save a checked URL for future scrape runs."""
    return await service.add_source(data.url, db)


@router.get("/sources")
async def list_sources(db: AsyncSession = Depends(get_db)) -> list[str]:
    """List sites included in Jobs page scrape runs."""
    return await service.list_source_urls(db)


@router.post("/import")
async def import_jobs(data: CrawlImportIn, db: AsyncSession = Depends(get_db)) -> CrawlImportOut:
    """Import the selected crawl results."""
    return await service.import_crawl_jobs(data.jobs, db)


@router.post("/runs", status_code=202)
async def start_run(data: SiteCheckIn, db: AsyncSession = Depends(get_db)) -> CrawlStatus:
    """Queue a background Site Check."""
    return await crawl_service.start(data.url, db)


@router.get("/runs/latest")
async def latest_run(db: AsyncSession = Depends(get_db)) -> CrawlStatus | None:
    """Reconnect to the latest crawl in this single-user app."""
    return await crawl_repository.latest(db)


@router.get("/runs/{run_id}/pages")
async def run_pages(
    run_id: UUID, offset: int = Query(0, ge=0), db: AsyncSession = Depends(get_db)
) -> list[SiteCheckOut]:
    """Read a batch of completed pages starting at the supplied offset."""
    return await crawl_repository.pages(run_id, offset, db)


@router.post("/runs/{run_id}/stop")
async def stop_run(run_id: UUID, db: AsyncSession = Depends(get_db)) -> CrawlStatus:
    """Stop a queued or running crawl."""
    return await crawl_service.stop(run_id, db)
