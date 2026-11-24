import asyncio
import logging
from collections import deque
from urllib.robotparser import RobotFileParser
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.jobs import service as jobs_service
from app.modules.scraper import service as scraper_service
from app.modules.scraper.schemas import JobIn
from app.modules.site_check import cambojob, repository
from app.modules.site_check.job_posting import extract_postings, page_links
from app.modules.site_check.safe_fetch import (
    Fetched,
    FetchError,
    fetch,
    parse_url,
    resolve_public_ip,
)
from app.modules.site_check.schemas import (
    CrawlImportOut,
    CrawlJob,
    RobotsStatus,
    ScrapeSiteOut,
    SiteCheckOut,
)
from app.shared.exceptions import BadRequest

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 10
PREVIEW_CHARS = 1500
MIN_USEFUL_CHARS = 200
BLOCKED_STATUSES = {401, 403, 407, 429}
NOT_A_GUARANTEE = (
    "A successful test does not guarantee permission for ongoing scraping; "
    "check the site's terms of service."
)


async def _robots_status(client: httpx.AsyncClient, url: httpx.URL) -> RobotsStatus:
    """robots.txt verdict for `url`, following RFC 9309 (4xx = no rules, 5xx = unreachable)."""
    try:
        robots = await fetch(client, url.copy_with(path="/robots.txt", query=None, fragment=None))
    except (FetchError, BadRequest):
        return "unavailable"
    if robots.status in BLOCKED_STATUSES:
        return "unavailable"
    if 400 <= robots.status < 500:
        return "not_found"
    if robots.status >= 300:
        return "unavailable"
    parser = RobotFileParser()
    parser.parse(robots.text.splitlines())
    return "allowed" if parser.can_fetch(scraper_service.USER_AGENT, str(url)) else "disallowed"


def _blocked_reason(page: Fetched, robots: RobotsStatus) -> tuple[str, str] | None:
    """(result, message) when we must not or could not extract content, else None."""
    if robots == "disallowed":
        return "restricted", (
            "robots.txt disallows automated access to this URL, so content was not fetched."
        )
    if robots == "unavailable":
        return "inconclusive", (
            "robots.txt could not be read (server error or timeout), so content was not fetched."
        )
    if page.status in BLOCKED_STATUSES:
        return "restricted", (
            f"The site refused access (HTTP {page.status}): login, rate limit or bot "
            "protection. This tool does not bypass access controls."
        )
    if page.status >= 400:
        return "failed", f"The site responded with an error (HTTP {page.status})."
    if "html" not in page.content_type and not page.content_type.startswith("text/"):
        kind = page.content_type or "unknown type"
        return "inconclusive", f"The URL returned non-HTML content ({kind})."
    return None


async def _assess(url: httpx.URL, page: Fetched, robots: RobotsStatus) -> SiteCheckOut:
    out = SiteCheckOut(
        url=str(url),
        final_url=str(page.url),
        http_status=page.status,
        robots_status=robots,
        result="successful",
        message="",
    )
    if blocked := _blocked_reason(page, robots):
        out.result, out.message = blocked  # type: ignore[assignment]
        return out
    text = await asyncio.to_thread(scraper_service.extract_text, page.text)
    if "captcha" in text.lower() and len(text) < 3000:
        out.result, out.message = "restricted", "The page shows a CAPTCHA or bot check."
    elif len(text) < MIN_USEFUL_CHARS:
        out.result = "inconclusive"
        out.message = (
            f"Only {len(text)} characters of text found: the page is nearly empty or "
            "renders its content with JavaScript."
        )
    else:
        out.message = f"Readable content extracted ({len(text)} characters). {NOT_A_GUARANTEE}"
    if out.result != "restricted":
        out.content_text = text or None
    out.content_preview = text[:PREVIEW_CHARS] or None
    return out


async def check_site(raw_url: str, origin: str | None = None) -> SiteCheckOut:
    """Check one page and return the same-site links for continuing the crawl."""
    result, jobs = await _inspect(raw_url, origin)
    result.jobs = [CrawlJob.model_validate(job) for job in jobs]
    return result


async def _inspect(raw_url: str, origin: str | None) -> tuple[SiteCheckOut, list[JobIn]]:
    result, page = await _check_page(raw_url, origin)
    if page is None or result.result == "restricted" or _blocked_reason(page, result.robots_status):
        return result, []
    url = str(page.url)
    if page.url.host in {"www.cambojob.com", "cambojob.com"} and "html" in page.content_type:
        jobs = await asyncio.to_thread(cambojob.inspect_page, page.text, result)
    else:
        jobs = await asyncio.to_thread(lambda: list(extract_postings(page.text, url)))
        result.job_urls = [job.url for job in jobs]
        result.job_count = len(jobs)
        if "html" in page.content_type:
            result.links = await asyncio.to_thread(page_links, page.text, url)
    return result, [
        j for j in jobs if j.title.strip() and j.description.strip() and len(j.url) <= 2048
    ]


def _check_origin(url: httpx.URL, origin: str | None) -> None:
    if origin and url.copy_with(path="/", query=None, fragment=None) != parse_url(origin).copy_with(
        path="/", query=None, fragment=None
    ):
        raise BadRequest("This link leaves the website being crawled.")


async def _check_page(
    raw_url: str, origin: str | None = None
) -> tuple[SiteCheckOut, Fetched | None]:
    url = parse_url(raw_url).copy_with(fragment=None)
    _check_origin(url, origin)
    async with httpx.AsyncClient(
        timeout=TIMEOUT_SECONDS,
        follow_redirects=False,
        trust_env=False,
        headers={"User-Agent": scraper_service.USER_AGENT},
    ) as client:
        try:
            await resolve_public_ip(url)  # fail fast with 400 before any request
            robots = await _robots_status(client, url)
            method = "GET" if robots in ("allowed", "not_found") else "HEAD"
            page = await fetch(
                client,
                url,
                method,
                check_redirect=lambda target: _check_redirect(client, target, method, origin),
            )
        except FetchError as exc:
            return (
                SiteCheckOut(
                    url=str(url), robots_status="unavailable", result="failed", message=str(exc)
                ),
                None,
            )
    logger.info("Site check %s: HTTP %s, robots %s", url.host, page.status, robots)
    return await _assess(url, page, robots), page


async def _check_redirect(
    client: httpx.AsyncClient, target: httpx.URL, method: str, origin: str | None
) -> None:
    _check_origin(target, origin)
    await resolve_public_ip(target)
    if method == "GET" and await _robots_status(client, target) not in ("allowed", "not_found"):
        raise BadRequest("The redirected URL does not allow automated access.")


async def add_source(raw_url: str, db: AsyncSession) -> ScrapeSiteOut:
    """Recheck a URL before persisting it as a source."""
    check, _ = await _check_page(raw_url)
    if check.result != "successful" or len(check.url) > 2048:
        raise BadRequest("Only URLs with a successful site check can be added.")
    site = await repository.save_url(check.url, db)
    return ScrapeSiteOut(id=site.id, url=site.url)


async def list_source_urls(db: AsyncSession) -> list[str]:
    """List checked URLs for the scraper worker."""
    return await repository.list_urls(db)


async def scrape_source(url: str) -> list[JobIn]:
    """Follow same-site links and collect unique jobs from a saved source."""
    pending = deque([url])
    seen = {url}
    origin = None
    jobs: dict[str, JobIn] = {}
    deadline = asyncio.get_running_loop().time() + 600
    while pending:
        try:
            async with asyncio.timeout_at(deadline):
                result, postings = await _inspect(pending.popleft(), origin)
        except TimeoutError:
            logger.warning("Saved source crawl reached its time limit; keeping %d jobs", len(jobs))
            break
        except BadRequest:
            continue
        origin = origin or result.final_url
        seen.add(result.final_url or result.url)
        for job in postings:
            jobs.setdefault(job.url, job)
        for link in result.links:
            if link not in seen:
                seen.add(link)
                pending.append(link)
    return list(jobs.values())


async def import_crawl_jobs(jobs: list[CrawlJob], db: AsyncSession) -> CrawlImportOut:
    """Save extracted titles and descriptions while preserving existing rows."""
    added = await jobs_service.save_scraped(
        [job.model_dump() | {"source": "website"} for job in jobs], db
    )
    return CrawlImportOut(added=added, skipped=len(jobs) - added)


async def run_background_crawl(run_id: UUID, db: AsyncSession) -> None:
    """Run the interactive crawl in a worker and publish failures to the browser."""
    from app.modules.site_check import crawl_repository, crawl_service

    try:
        await crawl_service.execute(run_id, db)
    except Exception:
        await db.rollback()
        await crawl_repository.finish(
            run_id, "failed", "The crawl failed. Completed pages are available.", db
        )
        raise
