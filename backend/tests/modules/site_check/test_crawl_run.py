from unittest.mock import AsyncMock, patch
from uuid import UUID

from app.modules.site_check import crawl_service
from app.modules.site_check.schemas import SiteCheckOut


async def test_background_crawl_reconnect_and_stop(client, db):
    root = "https://example.com/"
    child = root + "jobs"
    page = SiteCheckOut(
        url=root,
        robots_status="allowed",
        result="successful",
        message="ok",
        links=[child],
        job_urls=[child],
    )
    with patch.object(crawl_service, "_enqueue") as enqueue:
        run = (await client.post("/api/site-check/runs", json={"url": root})).json()
        same = (await client.post("/api/site-check/runs", json={"url": root})).json()
        assert same["id"] == run["id"] and run["status"] == "queued"
        enqueue.assert_called_once_with(UUID(run["id"]))
    with patch.object(
        crawl_service,
        "check_site",
        AsyncMock(side_effect=[page, page.model_copy(update={"url": child})]),
    ) as fetch:
        await crawl_service.execute(UUID(run["id"]), db)
        await crawl_service.execute(UUID(run["id"]), db)
        assert fetch.await_count == 2
    status = (await client.get("/api/site-check/runs/latest")).json()
    assert (status["status"], status["checked"], status["discovered"], status["job_count"]) == (
        "completed",
        2,
        2,
        1,
    )
    endpoint = "/api/site-check/runs/" + run["id"]
    assert [p["url"] for p in (await client.get(endpoint + "/pages?offset=1")).json()] == [child]
    with patch.object(crawl_service, "_enqueue"):
        another = (await client.post("/api/site-check/runs", json={"url": child})).json()["id"]
    assert (await client.post(f"/api/site-check/runs/{another}/stop")).json()["status"] == "stopped"
    with patch.object(crawl_service, "check_site", AsyncMock()) as fetch:
        await crawl_service.execute(UUID(another), db)
        fetch.assert_not_awaited()
