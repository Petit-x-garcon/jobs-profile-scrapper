"""Database checkpoints for background site crawls."""

from uuid import UUID

from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.site_check.models import CrawlPage, CrawlRun
from app.modules.site_check.schemas import CrawlStatus, SiteCheckOut
from app.shared.exceptions import NotFound

ACTIVE = ("queued", "running")


async def latest(db: AsyncSession) -> CrawlStatus | None:
    """Return the most recently requested crawl."""
    run = await db.scalar(select(CrawlRun).order_by(CrawlRun.created_at.desc()).limit(1))
    return CrawlStatus.model_validate(run) if run else None


async def create(url: str, db: AsyncSession) -> tuple[CrawlStatus, bool]:
    """Serialize starts for the single-user app and reuse an active run."""
    if db.get_bind().dialect.name == "postgresql":
        await db.execute(text("LOCK TABLE site_crawls IN SHARE ROW EXCLUSIVE MODE"))
    current = await latest(db)
    if current and current.status in ACTIVE:
        await db.commit()
        return current, False
    run = CrawlRun(url=url)
    db.add(run)
    await db.commit()
    return CrawlStatus.model_validate(run), True


async def get(run_id: UUID, db: AsyncSession) -> CrawlStatus:
    """Get a crawl by ID."""
    run = await db.get(CrawlRun, run_id, populate_existing=True)
    if run is None:
        raise NotFound("Crawl not found.")
    return CrawlStatus.model_validate(run)


async def pages(run_id: UUID, offset: int, db: AsyncSession) -> list[SiteCheckOut]:
    """Read the next batch of immutable completed page results."""
    stmt = (
        select(CrawlPage.result)
        .where(CrawlPage.run_id == run_id, CrawlPage.position >= offset)
        .order_by(CrawlPage.position)
        .limit(20)
    )
    return [SiteCheckOut.model_validate(row) for row in await db.scalars(stmt)]


async def advance(
    run_id: UUID, checked: int, values: dict, db: AsyncSession, page: SiteCheckOut | None = None
) -> bool:
    """Only the worker at the current checkpoint may advance an active run."""
    stmt = (
        update(CrawlRun)
        .where(CrawlRun.id == run_id, CrawlRun.status.in_(ACTIVE), CrawlRun.checked == checked)
        .values(**values)
        .returning(CrawlRun.id)
    )
    changed = await db.scalar(stmt)
    if changed and page is not None:
        db.add(CrawlPage(run_id=run_id, position=checked, result=page.model_dump(mode="json")))
    await db.commit()
    return changed is not None


async def finish(run_id: UUID, status: str, error: str | None, db: AsyncSession) -> None:
    """Stop a run without overwriting a previously recorded terminal state."""
    await db.execute(
        update(CrawlRun)
        .where(CrawlRun.id == run_id, CrawlRun.status.in_(ACTIVE))
        .values(status=status, current_url=None, error=error)
    )
    await db.commit()
