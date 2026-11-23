from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

from app.modules.ai.schemas import Enrichment
from app.modules.ai.service import AIUnavailable
from app.modules.jobs import repository, service


def _job(url: str, **kw) -> dict:
    base = {
        "source": "x",
        "url": url,
        "title": "T",
        "company": None,
        "location": None,
        "description": "d",
        "posted_at": None,
    }
    return base | kw


async def test_list_pagination_and_order(client, db):
    now = datetime.now(UTC)
    await repository.upsert_many(
        [
            _job("u1", score=10, scraped_at=now),
            _job("u2", score=90, scraped_at=now),
            _job("u3", scraped_at=now + timedelta(seconds=1)),
        ],
        db,
    )
    body = (await client.get("/api/jobs", params={"page": 1, "size": 2})).json()
    assert set(body) == {"items", "total", "page", "size"}
    assert (body["total"], body["page"], body["size"]) == (3, 1, 2)
    assert [i["url"] for i in body["items"]] == ["u2", "u1"]
    assert (await client.get("/api/jobs", params={"min_score": 50})).json()["total"] == 1
    assert (await client.get("/api/jobs", params={"size": 101})).status_code == 422


async def test_get_job_404(client):
    r = await client.get("/api/jobs/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404
    assert r.json() == {"detail": "Job not found."}


async def test_import_job(client, enqueue):
    r = await client.post(
        "/api/jobs/import", json={"url": None, "title": None, "text": "Dev\nbody"}
    )
    assert r.status_code == 201
    body = r.json()
    assert body["source"] == "manual"
    assert body["url"].startswith("manual:")
    assert body["title"] == "Dev"
    enqueue.assert_called_once()
    assert (await client.get(f"/api/jobs/{body['id']}")).status_code == 200


async def test_scrape_returns_task_id(client):
    with patch("app.modules.jobs.service.enqueue_scrape", return_value="abc") as m:
        r = await client.post("/api/scrape", json={})
    assert r.status_code == 202
    assert r.json() == {"task_id": "abc"}
    m.assert_called_once_with("IT")


async def test_upsert_skips_existing_urls(db):
    assert await repository.upsert_many([_job("u1")], db) == 1
    assert await repository.upsert_many([_job("u1"), _job("u2")], db) == 1


async def test_enrich_only_unenriched(db):
    await repository.upsert_many(
        [
            _job("done", summary="s", score=50),
            _job("new"),
            _job("rescore", summary="keep", score=None),
        ],
        db,
    )
    fake = AsyncMock(return_value=Enrichment(summary="new-s", score=70, reasons="r"))
    with patch("app.modules.jobs.service.ai.enrich", fake):
        assert await service.enrich_pending(db) == 2
        assert await service.enrich_pending(db) == 0
    assert fake.await_count == 2
    rows, _ = await repository.list_jobs(1, 10, None, None, db)
    by_url = {j.url: j for j in rows}
    assert by_url["done"].score == 50
    assert by_url["rescore"].summary == "keep"
    assert by_url["new"].summary == "new-s"


async def test_enrich_skips_when_ai_unavailable(db):
    await repository.upsert_many([_job("a")], db)
    with patch("app.modules.jobs.service.ai.enrich", AsyncMock(side_effect=AIUnavailable("x"))):
        assert await service.enrich_pending(db) == 0
    assert len(await repository.list_unenriched(db)) == 1
