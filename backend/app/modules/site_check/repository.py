from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.site_check.models import ScrapeSite


async def save_url(url: str, db: AsyncSession) -> ScrapeSite:
    """Save a URL once, including when concurrent requests add it."""
    query = select(ScrapeSite).where(ScrapeSite.url == url)
    if existing := await db.scalar(query):
        return existing
    site = ScrapeSite(url=url)
    try:
        async with db.begin_nested():
            db.add(site)
            await db.flush()
    except IntegrityError:
        if existing := await db.scalar(query):
            return existing
        raise
    await db.commit()
    return site


async def list_urls(db: AsyncSession) -> list[str]:
    """Return URLs registered for scraping."""
    return list(await db.scalars(select(ScrapeSite.url).order_by(ScrapeSite.url)))
