"""Service tests: adapters are mocked, no network."""

from unittest.mock import AsyncMock, patch

import pytest

from app.modules.scraper import service
from app.modules.scraper.schemas import JobIn

pytestmark = pytest.mark.asyncio


def _job(source: str, url: str) -> JobIn:
    return JobIn(source=source, url=url, title="t", description="d")


async def test_failing_adapter_is_skipped() -> None:
    with (
        patch.object(service.dodojob, "fetch", AsyncMock(side_effect=RuntimeError("boom"))),
        patch.object(service.jobify, "fetch", AsyncMock(return_value=[_job("jobify", "u1")])),
    ):
        jobs = await service.scrape("IT")
    assert [j.url for j in jobs] == ["u1"]


async def test_dedupes_by_url() -> None:
    with (
        patch.object(service.dodojob, "fetch", AsyncMock(return_value=[_job("dodojob", "same")])),
        patch.object(
            service.jobify,
            "fetch",
            AsyncMock(return_value=[_job("jobify", "same"), _job("jobify", "other")]),
        ),
    ):
        jobs = await service.scrape("IT")
    assert [j.url for j in jobs] == ["same", "other"]
