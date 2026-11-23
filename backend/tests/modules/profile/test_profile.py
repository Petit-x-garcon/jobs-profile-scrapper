from app.modules.jobs import repository

PUT = {
    "headline": "H",
    "skills": ["a"],
    "years_experience": 5,
    "locations": ["X"],
    "remote_ok": False,
    "min_salary": 1000,
    "summary": "S",
}

JOB = {
    "source": "x",
    "url": "u",
    "title": "T",
    "company": None,
    "location": None,
    "description": "d",
    "posted_at": None,
    "summary": "keep",
    "score": 80,
    "match_reason": "why",
}


async def test_get_seeds_then_put_resets_scores(client, db, enqueue):
    r = await client.get("/api/profile")
    assert r.status_code == 200
    assert r.json()["headline"].startswith("Full-stack Developer (sample")
    assert r.json()["skills"][0] == "Python"

    await repository.upsert_many([JOB], db)
    r = await client.put("/api/profile", json=PUT)
    assert r.status_code == 200
    assert r.json()["years_experience"] == 5
    assert (await client.get("/api/profile")).json()["headline"] == "H"
    enqueue.assert_called_once()

    job = (await client.get("/api/jobs")).json()["items"][0]
    assert (job["score"], job["match_reason"], job["summary"]) == (None, None, "keep")
