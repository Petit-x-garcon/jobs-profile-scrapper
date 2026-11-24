from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from app.modules.jobs import repository


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
            _job("u1", score=10, scraped_at=now - timedelta(seconds=1)),
            _job("u2", score=90, scraped_at=now),
            _job("u3", scraped_at=now + timedelta(seconds=1)),
        ],
        db,
    )
    body = (await client.get("/api/jobs", params={"page": 1, "size": 2})).json()
    assert set(body) == {"items", "total", "page", "size"}
    assert (body["total"], body["page"], body["size"]) == (3, 1, 2)
    assert [i["url"] for i in body["items"]] == ["u3", "u2"]
    assert (await client.get("/api/jobs", params={"min_score": 50})).json()["total"] == 1
    assert (await client.get("/api/jobs", params={"size": 101})).status_code == 422


async def test_keyword_filter(client, db):
    await repository.upsert_many(
        [
            _job("ai", title="AI Engineer", description="Python, remote friendly"),
            _job("be", title="Backend Developer", location="Remote"),
            _job("pct", title="100% Sales"),
            _job("maint", title="Maintenance Lead", description="Send email updates"),
            _job("cpp", title="Developer", description="Strong C++ and Node.js skills"),
        ],
        db,
    )

    async def urls(q: str) -> set[str]:
        body = (await client.get("/api/jobs", params={"q": q})).json()
        return {i["url"] for i in body["items"]}

    assert await urls("ai engineer") == {"ai"}  # phrase, case-insensitive
    assert await urls("remote") == {"ai", "be"}  # matches description and location
    assert await urls("Python, Remote") == {"ai"}  # every keyword must match
    assert await urls("AI") == {"ai"}  # whole word: not "mAIntenance" or "emAIl"
    assert await urls("100%") == {"pct"}
    assert await urls("c++, node.js") == {"cpp"}  # regex characters are literal
    assert await urls(".") == set()
    assert len(await urls(" , ")) == 5


async def test_get_job_404(client):
    r = await client.get("/api/jobs/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404
    assert r.json() == {"detail": "Job not found."}


async def test_import_job_does_not_call_ai(client):
    with patch("app.modules.ai.service.enrich") as enrich:
        r = await client.post(
            "/api/jobs/import", json={"url": None, "title": None, "text": "Dev\nbody"}
        )
    assert r.status_code == 201
    body = r.json()
    assert body["source"] == "manual"
    assert body["url"].startswith("manual:")
    assert body["title"] == "Dev"
    assert body["score"] is None
    enrich.assert_not_called()
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
