"""Discover CamboJob's server-rendered tab panels, directory pages and job details."""

import re

import httpx
from bs4 import BeautifulSoup

from app.modules.scraper.schemas import JobIn
from app.modules.site_check.schemas import SiteCheckOut

_JOB = re.compile(r"/jobs/jobs-show-\d+[^/]*\.htm", re.I)
_DIRECTORY = re.compile(r"/jobs/jobs_list(?:/page/\d+)?\.htm", re.I)


def inspect_page(html: str, result: SiteCheckOut) -> list[JobIn]:
    """Populate discovered links and counts, returning importable job details."""
    base = httpx.URL(result.final_url or result.url)
    soup = BeautifulSoup(html, "lxml")
    jobs: dict[str, None] = {}
    directory: dict[str, None] = {}
    for tag in soup.select("a[href], [data-href], [data-url]"):
        href = str(tag.get("data-href") or tag.get("data-url") or tag.get("href"))
        try:
            target = base.join(href).copy_with(fragment=None)
        except (httpx.InvalidURL, ValueError):
            continue
        if target.netloc != base.netloc or target.scheme != base.scheme or target.userinfo:
            continue
        if _JOB.fullmatch(target.path):
            jobs[str(target)] = None
        elif _DIRECTORY.fullmatch(target.path):
            directory[str(target.copy_with(path=target.path.lower()))] = None

    labels = soup.select(
        "[data-event=new_job], [data-event=popular_job], [data-event=high_salary_job]"
    )
    for label, panel in zip(labels, soup.select("#jobsContent .content-part2"), strict=False):
        titles = [node.get_text(strip=True) for node in panel.select(".left h3[data-href]")]
        result.job_tabs[label.get_text(strip=True)] = titles

    result.links = list(directory) + list(jobs)
    postings = []
    if _JOB.fullmatch(base.path):
        title = soup.select_one(".job-detail-left .jobs_name")
        description = soup.select_one(".job-desc .job-news-body")
        company = soup.select_one("h3 a[href*='/company/company-show-']")
        if title and description:
            postings.append(
                JobIn(
                    source="website",
                    url=str(base),
                    title=title.get_text(strip=True)[:500],
                    description=description.get_text("\n", strip=True),
                    company=company.get_text(strip=True)[:300] if company else None,
                )
            )
            jobs[str(base)] = None
    result.job_urls = list(jobs)
    result.job_count = len(jobs)
    return postings
