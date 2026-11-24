import uuid
from unittest.mock import AsyncMock, patch

from app.modules.ai.schemas import Enrichment
from app.modules.ai.service import AIBadResponse, AIUnavailable
from app.modules.jobs import repository
from app.modules.jobs.schemas import JobQuery

ENRICH = "app.modules.recommendations.service.ai.enrich"


def _job(url: str, **kw) -> dict:
    return {"source": "x", "url": url, "title": url, "description": "d"} | kw


async def _ids(db) -> dict[str, str]:
    rows, _ = await repository.list_jobs(JobQuery(), 1, 100, db)
    return {j.url: str(j.id) for j in rows}


def _result(score: int) -> Enrichment:
    return Enrichment(
        summary="s", score=score, reasons="r", matching_skills=["py"], missing_skills=["go"]
    )


async def test_analyze_ranks_saves_and_reuses(client, db):
    await repository.upsert_many([_job("low"), _job("high"), _job("cached", score=50)], db)
    ids = await _ids(db)
    fake = AsyncMock(side_effect=lambda text, _: _result(90 if text.startswith("high") else 10))
    with patch(ENRICH, fake):
        r = await client.post("/api/recommendations", json={"job_ids": list(ids.values())})
        assert r.status_code == 200
        body = r.json()
        assert [i["url"] for i in body["items"]] == ["high", "cached", "low"]
        assert (body["analyzed"], body["failed"]) == (2, 0)
        assert body["items"][0]["missing_skills"] == ["go"]
        assert fake.await_count == 2  # the cached job was not re-analyzed

        again = await client.post("/api/recommendations", json={"job_ids": [ids["high"]]})
        assert again.json()["analyzed"] == 0
        assert fake.await_count == 2


async def test_profile_change_forces_reanalysis(client, db):
    await repository.upsert_many([_job("a")], db)
    ids = await _ids(db)
    fake = AsyncMock(return_value=_result(70))
    with patch(ENRICH, fake):
        await client.post("/api/recommendations", json={"job_ids": [ids["a"]]})
        profile = (await client.get("/api/profile")).json()
        await client.put("/api/profile", json=profile | {"skills": ["Go"]})
        await client.post("/api/recommendations", json={"job_ids": [ids["a"]]})
    assert fake.await_count == 2
    assert "Go" in fake.await_args.args[1]  # latest profile was sent


async def test_partial_failure_is_reported(client, db):
    await repository.upsert_many([_job("ok"), _job("bad")], db)
    ids = await _ids(db)

    async def flaky(text: str, _: str) -> Enrichment:
        if text.startswith("bad"):
            raise AIBadResponse("x")
        return _result(60)

    with patch(ENRICH, flaky):
        body = (
            await client.post("/api/recommendations", json={"job_ids": list(ids.values())})
        ).json()
    assert [i["url"] for i in body["items"]] == ["ok"]
    assert (body["analyzed"], body["failed"]) == (1, 1)


async def test_ai_unavailable_and_validation(client, db):
    await repository.upsert_many([_job("a")], db)
    ids = await _ids(db)
    with patch(ENRICH, AsyncMock(side_effect=AIUnavailable("Azure OpenAI is not configured."))):
        r = await client.post("/api/recommendations", json={"job_ids": [ids["a"]]})
    assert r.status_code == 503
    assert r.json() == {"detail": "Azure OpenAI is not configured."}

    missing = await client.post("/api/recommendations", json={"job_ids": [str(uuid.uuid4())]})
    assert missing.status_code == 404
    assert (await client.post("/api/recommendations", json={"job_ids": []})).status_code == 422
    too_many = [str(uuid.uuid4()) for _ in range(21)]
    assert (
        await client.post("/api/recommendations", json={"job_ids": too_many})
    ).status_code == 422
