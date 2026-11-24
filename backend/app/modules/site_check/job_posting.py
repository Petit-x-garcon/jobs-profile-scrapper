import hashlib
import json
from collections.abc import Iterator

import httpx
from bs4 import BeautifulSoup, Tag

from app.modules.scraper.schemas import JobIn
from app.modules.site_check.safe_fetch import parse_url
from app.shared.exceptions import BadRequest


def _postings(value: object) -> Iterator[dict[str, object]]:
    if isinstance(value, list):
        for item in value:
            yield from _postings(item)
    elif isinstance(value, dict):
        kind = value.get("@type")
        if kind == "JobPosting" or (isinstance(kind, list) and "JobPosting" in kind):
            yield value
        yield from _postings(value.get("@graph"))
        yield from _postings(value.get("mainEntity"))
        yield from _postings(value.get("itemListElement"))
        yield from _postings(value.get("item"))


def page_links(html: str, url: str) -> list[str]:
    """Discover same-origin links, preserving pagination queries and dropping fragments."""
    base = httpx.URL(url)
    links: dict[str, None] = {}
    for tag in BeautifulSoup(html, "lxml").select("a[href], link[rel~=next][href]"):
        target = _web_url(base, str(tag["href"]))
        if target and target.copy_with(path="/", query=None) == base.copy_with(
            path="/", query=None
        ):
            links[str(target)] = None
    return list(links)


def _web_url(base: httpx.URL, href: str) -> httpx.URL | None:
    try:
        target = parse_url(str(base.join(href))).copy_with(fragment=None)
    except (BadRequest, httpx.InvalidURL, ValueError):
        return None
    return target if len(str(target)) <= 2048 else None


def extract_postings(html: str, url: str) -> Iterator[JobIn]:
    """Yield structured jobs with distinct URLs for the jobs repository."""
    used: set[str] = set()
    fallback_keys: set[str] = set()
    for tag in BeautifulSoup(html, "lxml").find_all("script", type="application/ld+json"):
        if not isinstance(tag, Tag) or tag.string is None:
            continue
        try:
            metadata = json.loads(tag.string)
        except (ValueError, RecursionError):
            continue
        for posting in _postings(metadata):
            title = posting.get("title")
            description = posting.get("description")
            if not isinstance(title, str) or not isinstance(description, str):
                continue
            text = BeautifulSoup(description, "lxml").get_text("\n", strip=True)
            if not title.strip() or not text:
                continue
            organization = posting.get("hiringOrganization")
            name = organization.get("name") if isinstance(organization, dict) else None
            href = posting.get("url")
            target = _web_url(httpx.URL(url), href) if isinstance(href, str) else None
            job_url = str(target or url)
            if not target:
                identity = json.dumps(
                    [title, name, posting.get("identifier") or text], sort_keys=True
                )
                digest = hashlib.sha256(identity.encode()).hexdigest()[:20]
                if digest in fallback_keys:
                    continue
                fallback_keys.add(digest)
                if job_url in used:
                    job_url = f"{url}#job-{digest}"
            if job_url in used or len(job_url) > 2048:
                continue
            used.add(job_url)
            yield JobIn(
                source="website",
                url=job_url,
                title=title.strip()[:500],
                company=name.strip()[:300] or None if isinstance(name, str) else None,
                description=text,
            )
