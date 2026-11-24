import asyncio
import logging
from urllib.robotparser import RobotFileParser

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.scraper import service as scraper_service
from app.modules.scraper.schemas import JobIn
from app.modules.site_check import repository
from app.modules.site_check.job_posting import extract_posting
from app.modules.site_check.safe_fetch import (
    Fetched,
    FetchError,
    fetch,
    parse_url,
    resolve_public_ip,
)
from app.modules.site_check.schemas import RobotsStatus, ScrapeSiteOut, SiteCheckOut
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
    out.content_preview = text[:PREVIEW_CHARS] or None
    return out


async def check_site(raw_url: str) -> SiteCheckOut:
    """Test whether a public URL is reachable, allowed by robots.txt, and has extractable text.

    Raises BadRequest for invalid or unsafe (private/internal) URLs. Content is only
    downloaded when robots.txt permits it; otherwise a HEAD request reports the status.
    """
    result, _ = await _check_page(raw_url)
    return result


async def _check_page(raw_url: str) -> tuple[SiteCheckOut, Fetched | None]:
    url = parse_url(raw_url).copy_with(fragment=None)
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
                check_redirect=lambda target: (
                    _check_redirect(client, target) if method == "GET" else None
                ),
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


async def _check_redirect(client: httpx.AsyncClient, target: httpx.URL) -> None:
    await resolve_public_ip(target)
    if await _robots_status(client, target) not in ("allowed", "not_found"):
        raise BadRequest("The redirected URL does not allow automated access.")


async def add_source(raw_url: str, db: AsyncSession) -> ScrapeSiteOut:
    """Recheck a URL before persisting it as a source."""
    check = await check_site(raw_url)
    if check.result != "successful" or len(check.url) > 2048:
        raise BadRequest("Only URLs with a successful site check can be added.")
    site = await repository.save_url(check.url, db)
    return ScrapeSiteOut(id=site.id, url=site.url)


async def list_source_urls(db: AsyncSession) -> list[str]:
    """List checked URLs for the scraper worker."""
    return await repository.list_urls(db)


async def scrape_source(url: str) -> JobIn | None:
    """Recheck access and extract a structured posting from a saved URL."""
    try:
        check, page = await _check_page(url)
    except BadRequest:
        return None
    if check.result != "successful" or page is None or len(str(page.url)) > 2048:
        return None
    return await asyncio.to_thread(extract_posting, page.text, str(page.url))
