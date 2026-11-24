from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.site_check import service
from app.modules.site_check.schemas import ScrapeSiteOut, SiteCheckIn, SiteCheckOut

router = APIRouter(prefix="/site-check", tags=["site-check"])


@router.post("")
async def check_site(data: SiteCheckIn) -> SiteCheckOut:
    """Test whether a website can be scraped (public, single-user app).

    400 for invalid URLs and for private/internal targets (SSRF protection).
    """
    return await service.check_site(data.url)


@router.post("/sources", status_code=201)
async def add_source(data: SiteCheckIn, db: AsyncSession = Depends(get_db)) -> ScrapeSiteOut:
    """Save a checked URL for future scrape runs."""
    return await service.add_source(data.url, db)
