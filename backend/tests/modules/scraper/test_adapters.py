"""Offline parse tests for the site adapters, using saved samples."""

from datetime import UTC, datetime
from pathlib import Path

from app.modules.scraper.adapters import dodojob, jobify

FIXTURES = Path(__file__).parent / "fixtures"
NOW = datetime(2026, 11, 13, 12, tzinfo=UTC)


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_dodojob_parse_list() -> None:
    jobs = dodojob.parse_list(_read("dodojob_list.html"), now=NOW)
    assert len(jobs) == 3
    job = jobs[0]
    assert job.source == "dodojob"
    assert job.url.startswith("https://www.dodojob.com/en/jobs/")
    assert job.title and job.company and job.location
    assert job.posted_at is not None and job.posted_at < NOW


def test_dodojob_parse_detail() -> None:
    text = dodojob.parse_detail(_read("dodojob_detail.html"))
    assert text.startswith("Requirements")
    assert "Benefits" in text
    assert "Work Location" not in text


def test_jobify_parse_list() -> None:
    jobs = jobify.parse_list(_read("jobify_list.json"))
    assert jobs
    job = jobs[0]
    assert job.source == "jobify"
    assert job.url.startswith("https://jobify.works/jobs/")
    assert job.title
    assert job.posted_at is not None and job.posted_at.tzinfo is not None


def test_jobify_parse_detail() -> None:
    text = jobify.parse_detail(_read("jobify_detail.json"))
    assert "<" not in text
    assert "Requirements" in text
    assert "Content planning and publishing" in text
