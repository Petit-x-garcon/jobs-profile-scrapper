"""Helpers shared by the site adapters."""

import asyncio
import logging
from collections.abc import Callable

import httpx
from bs4 import BeautifulSoup

from app.modules.scraper.schemas import JobIn

logger = logging.getLogger(__name__)

USER_AGENT = "job-scrapper/0.1 (personal job search tool)"
DETAIL_DELAY_SECONDS = 1.0


def html_to_text(html: str) -> str:
    """Convert an HTML fragment to plain text, one block per line."""
    return BeautifulSoup(html, "lxml").get_text("\n", strip=True)


async def add_descriptions(
    client: httpx.AsyncClient,
    jobs: list[JobIn],
    detail_url: Callable[[JobIn], str],
    parse_detail: Callable[[str], str],
) -> list[JobIn]:
    """Fetch each job's detail page one at a time (polite) and fill `description`.

    A job whose detail request fails is logged and dropped.
    """
    done: list[JobIn] = []
    for job in jobs:
        await asyncio.sleep(DETAIL_DELAY_SECONDS)
        try:
            response = await client.get(detail_url(job))
            response.raise_for_status()
            done.append(job.model_copy(update={"description": parse_detail(response.text)}))
        except httpx.HTTPError:
            logger.warning("detail fetch failed for %s", job.url, exc_info=True)
    return done
