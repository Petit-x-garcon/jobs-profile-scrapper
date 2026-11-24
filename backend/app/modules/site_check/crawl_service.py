"""Schedule and resume interactive crawls independently of their browser clients."""

import asyncio
from collections import deque
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.site_check import crawl_repository as repo
from app.modules.site_check.safe_fetch import parse_url
from app.modules.site_check.schemas import CrawlStatus, SiteCheckOut
from app.modules.site_check.service import check_site
from app.shared.exceptions import BadRequest


class Frontier:
    """Track the remaining links and distinct jobs across committed pages."""

    def __init__(self, url: str) -> None:
        self.pending = deque([url])
        self.seen = {url}
        self.discovered = 1
        self.jobs: set[str] = set()
        self.origin: str | None = None
        self.checked = 0

    def record(self, page: SiteCheckOut) -> None:
        """Advance exactly one page in breadth-first order."""
        self.pending.popleft()
        self.origin = self.origin or page.final_url or page.url
        self.seen.add(page.final_url or page.url)
        self.jobs.update(page.job_urls)
        for link in page.links:
            if link not in self.seen:
                self.pending.append(link)
                self.seen.add(link)
                self.discovered += 1
        self.checked += 1


def _enqueue(run_id: UUID) -> None:
    from app.tasks import crawl_website

    crawl_website.delay(str(run_id))


async def start(url: str, db: AsyncSession) -> CrawlStatus:
    """Queue a crawl and return the persisted run for reconnecting clients."""
    url = str(parse_url(url).copy_with(fragment=None))
    run, created = await repo.create(url, db)
    if not created:
        return run
    try:
        await asyncio.to_thread(_enqueue, run.id)
    except Exception:
        await repo.finish(
            run.id, "failed", "Could not queue the crawl. Check the worker and Redis.", db
        )
        return await repo.get(run.id, db)
    return run


async def stop(run_id: UUID, db: AsyncSession) -> CrawlStatus:
    """Stop at the last committed page."""
    await repo.finish(run_id, "stopped", None, db)
    return await repo.get(run_id, db)


async def execute(run_id: UUID, db: AsyncSession) -> None:
    """Resume the durable frontier and checkpoint each result before fetching another."""
    run = await repo.get(run_id, db)
    if run.status not in repo.ACTIVE:
        return
    frontier = Frontier(run.url)
    while frontier.checked < run.checked:
        for page in await repo.pages(run.id, frontier.checked, db):
            frontier.record(page)
    while frontier.pending:
        url = frontier.pending[0]
        checked = frontier.checked
        if not await repo.advance(run.id, checked, {"status": "running", "current_url": url}, db):
            return
        try:
            page = await check_site(url, frontier.origin)
        except BadRequest as exc:
            if not checked:
                await repo.finish(run.id, "failed", exc.detail, db)
                return
            page = SiteCheckOut(
                url=url, result="failed", robots_status="unavailable", message=exc.detail
            )
        frontier.record(page)
        values = dict(
            checked=frontier.checked,
            discovered=frontier.discovered,
            job_count=len(frontier.jobs),
            status="running" if frontier.pending else "completed",
            current_url=frontier.pending[0] if frontier.pending else None,
        )
        if not await repo.advance(run.id, checked, values, db, page):
            return
