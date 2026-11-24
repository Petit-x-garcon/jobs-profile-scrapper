import json
from collections.abc import Iterator

from bs4 import BeautifulSoup, Tag

from app.modules.scraper.schemas import JobIn


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


def extract_posting(html: str, url: str) -> JobIn | None:
    """Extract a job structured as schema.org JobPosting on the checked URL."""
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
            return JobIn(
                source="website",
                url=url,
                title=title.strip()[:500],
                company=name.strip()[:300] or None if isinstance(name, str) else None,
                description=text,
            )
    return None
