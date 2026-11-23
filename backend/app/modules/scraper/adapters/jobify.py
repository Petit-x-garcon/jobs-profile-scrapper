"""Jobify (Cambodia) adapter: public JSON API used by the site's own frontend."""

import json
from datetime import datetime

import httpx

from app.modules.scraper.adapters._common import add_descriptions, html_to_text
from app.modules.scraper.schemas import JobIn

API_URL = "https://api-v1.jobify.works/api/v1"
SITE_URL = "https://jobify.works"
SOURCE = "jobify"
_SECTIONS = (
    ("description", ""),
    ("responsible", "Responsibilities"),
    ("requirement", "Requirements"),
    ("employee_benefit", "Benefits"),
)


def parse_list(payload: str) -> list[JobIn]:
    """Parse the `/jobposts` JSON into jobs with an empty description."""
    rows = json.loads(payload)["job_posts"]["data"]
    return [
        JobIn(
            source=SOURCE,
            url=f"{SITE_URL}/jobs/{row['id']}",
            title=row["job_title"].strip(),
            company=row.get("company_name"),
            location=", ".join(p for p in (row.get("district"), row.get("city_province")) if p)
            or None,
            description="",
            posted_at=datetime.fromisoformat(row["created_at"]) if row.get("created_at") else None,
        )
        for row in rows
        if row.get("status") == "active"
    ]


def parse_detail(payload: str) -> str:
    """Return the plain-text description from a `/jobposts/{id}` JSON body."""
    post = json.loads(payload)["job_post"]
    parts: list[str] = []
    for key, heading in _SECTIONS:
        if post.get(key):
            parts += ([heading] if heading else []) + [html_to_text(post[key])]
    return "\n".join(parts)


def _detail_url(job: JobIn) -> str:
    return f"{API_URL}/jobposts/{job.url.rsplit('/', 1)[1]}"


async def fetch(client: httpx.AsyncClient, query: str, limit: int) -> list[JobIn]:
    """Search Jobify and return up to `limit` jobs with full descriptions."""
    params = {"search": query, "page": 1, "per_page": limit}
    response = await client.get(f"{API_URL}/jobposts", params=params)
    response.raise_for_status()
    jobs = parse_list(response.text)[:limit]
    return await add_descriptions(client, jobs, _detail_url, parse_detail)
