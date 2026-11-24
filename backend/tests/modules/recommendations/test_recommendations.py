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


async def test_preview_across_pages_then_analyze_only_selected(client, db):
    from datetime import UTC, datetime, timedelta

    profile = (await client.get("/api/profile")).json()
    await client.put(
        "/api/profile",
        json=profile
        | {
            "headline": "Backend Developer",
            "skills": ["Python", "python", "C++", "AI"],
            "experience": [{"title": "QA Lead", "company": "Example", "dates": ""}],
        },
    )
    now = datetime.now(UTC)
    old = now - timedelta(days=30)
    await repository.upsert_many(
        [
            _job("cached-role", title="Senior Backend Developer", scraped_at=old, score=70),
            _job("previous-role", title="QA Lead", description="Python", scraped_at=old),
            _job("two-skills", description="Python and C++", scraped_at=old),
            _job("one-skill", description="Python " * 20, scraped_at=now),
            _job("no-match", description="Maintain order"),
            _job("other", source="other", title="Backend Developer"),
            *[_job(f"recent-{n}") for n in range(25)],
        ],
        db,
    )
    path = "/api/recommendations/rankings"
    ids = await _ids(db)
    with patch(ENRICH, AsyncMock(return_value=_result(90))) as ai:
        first = (await client.get(path, params={"source": "x"})).json()
        legacy_path = "/api/recommendations/shortlist"
        legacy = (await client.get(legacy_path, params={"source": "x"})).json()
        assert isinstance(legacy, list)
        assert [item["id"] for item in legacy] == [row["job"]["id"] for row in first["items"][:4]]
        assert legacy[0]["title"] == "QA Lead" and legacy[1]["analyzed"]
        assert (await client.get(legacy_path, params={"source": "x", "page": 1})).json() == first
        items = first["items"]
        assert (first["total"], first["size"], first["page"]) == (30, 10, 1)
        assert [j["job"]["id"] for j in items[:4]] == [
            ids[k] for k in ("previous-role", "cached-role", "two-skills", "one-skill")
        ]
        assert items[0]["role_match"] and items[1]["job"]["score"] == 70
        assert items[2]["matching_skills"] == ["Python", "C++"]
        assert items[3]["matching_skills"] == ["Python"]
        assert (await client.get(path, params={"q": "missing"})).json()["total"] == 0
        assert [
            j["job"]["id"]
            for j in (await client.get(path, params={"min_score": 60})).json()["items"]
        ] == [ids["cached-role"]]
        ai.assert_not_awaited()
        result = (
            await client.post(
                "/api/recommendations",
                json={"job_ids": [items[0]["job"]["id"], items[1]["job"]["id"]]},
            )
        ).json()
        assert result["analyzed"] == 1
        assert ai.await_args.args[0].startswith("QA Lead\n")

    await repository.upsert_many(
        [
            _job(f"extra-{n}", description="Python", scraped_at=now + timedelta(minutes=n + 1))
            for n in range(12)
        ],
        db,
    )
    limited = (await client.get(path, params={"source": "x"})).json()
    assert len(limited["items"]) == 10
    assert limited["items"][3]["job"]["title"] == "extra-11"
    rows = limited["items"][:]
    for page in range(2, 6):
        rows.extend((await client.get(path, params={"source": "x", "page": page})).json()["items"])
    assert [row["rank"] for row in rows] == list(range(1, 43))
    assert len({row["job"]["id"] for row in rows}) == 42
    assert not rows[-1]["role_match"] and not rows[-1]["matching_skills"]
    with patch(ENRICH, AsyncMock(return_value=_result(50))) as ai:
        final_ids = [row["job"]["id"] for row in rows[40:]]
        result = (await client.post("/api/recommendations", json={"job_ids": final_ids})).json()
        assert {item["id"] for item in result["items"]} == set(final_ids)
        assert ai.await_count == 2
