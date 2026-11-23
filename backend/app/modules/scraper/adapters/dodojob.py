"""DodoJob adapter: server-rendered HTML (no JSON-LD or public API found)."""

import re
from datetime import UTC, datetime, timedelta
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.modules.scraper.adapters._common import add_descriptions, html_to_text
from app.modules.scraper.schemas import JobIn

BASE_URL = "https://www.dodojob.com"
SOURCE = "dodojob"
_AGO = re.compile(r"(\d+)\s*(minute|hour|day|week|month)s?\s+ago", re.IGNORECASE)
_UNIT_DAYS = {"minute": 1 / 1440, "hour": 1 / 24, "day": 1, "week": 7, "month": 30}


def _parse_ago(text: str, now: datetime) -> datetime | None:
    match = _AGO.search(text)
    if not match:
        return None
    return now - timedelta(days=int(match[1]) * _UNIT_DAYS[match[2].lower()])


def parse_list(html: str, now: datetime | None = None) -> list[JobIn]:
    """Parse the search page into jobs with an empty description."""
    now = now or datetime.now(UTC)
    jobs = []
    for card in BeautifulSoup(html, "lxml").select('a[href^="/en/jobs/"]'):
        title, company = card.find("h3"), card.find("p")
        if not title:
            continue
        icon = card.select_one("span.flex svg")
        age = card.select_one("span.text-xs")
        jobs.append(
            JobIn(
                source=SOURCE,
                url=urljoin(BASE_URL, str(card["href"])),
                title=title.get_text(strip=True),
                company=company.get_text(strip=True) if company else None,
                location=icon.parent.get_text(strip=True) if icon else None,
                description="",
                posted_at=_parse_ago(age.get_text(), now) if age else None,
            )
        )
    return jobs


def parse_detail(html: str) -> str:
    """Return the plain-text description (requirements and benefits) of a job page."""
    main = BeautifulSoup(html, "lxml").find("main")
    text = main.get_text("\n", strip=True) if main else html_to_text(html)
    start = text.find("Requirements")
    end = text.find("Work Location")
    return text[max(start, 0) : end if end > start else None].strip()


async def fetch(client: httpx.AsyncClient, query: str, limit: int) -> list[JobIn]:
    """Search DodoJob and return up to `limit` jobs with full descriptions."""
    response = await client.get(f"{BASE_URL}/en/jobs", params={"q": query})
    response.raise_for_status()
    # shortcut: only the first results page (~20 jobs); no pagination param found.
    jobs = list({j.url: j for j in parse_list(response.text)}.values())[:limit]
    return await add_descriptions(client, jobs, lambda j: j.url, parse_detail)
