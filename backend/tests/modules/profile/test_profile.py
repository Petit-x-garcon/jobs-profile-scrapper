from app.modules.jobs import repository

PUT = {
    "headline": "H",
    "skills": ["a"],
    "years_experience": 5,
    "locations": ["X"],
    "remote_ok": False,
    "min_salary": 1000,
    "summary": "S",
    "education": ["BSc CS"],
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
    "matching_skills": ["a"],
    "missing_skills": ["b"],
}


async def test_get_seeds_then_put_resets_scores(client, db):
    r = await client.get("/api/profile")
    assert r.status_code == 200
    assert r.json()["headline"].startswith("Full-stack Developer (sample")
    assert r.json()["skills"][0] == "Python"
    assert r.json()["experience"] == []

    await repository.upsert_many([JOB], db)
    r = await client.put("/api/profile", json=PUT)
    assert r.status_code == 200
    assert r.json()["years_experience"] == 5
    got = (await client.get("/api/profile")).json()
    assert (got["headline"], got["education"], got["projects"]) == ("H", ["BSc CS"], [])

    job = (await client.get("/api/jobs")).json()["items"][0]
    assert (job["score"], job["match_reason"], job["summary"]) == (None, None, "keep")
    assert (job["matching_skills"], job["missing_skills"]) == (None, None)


async def test_cv_sections_round_trip(client):
    work = {"company": "Example", "title": "Developer", "dates": "2024–Present"}
    education = {"degree": "BSc", "university": "Example University", "year": "2023"}
    response = await client.put(
        "/api/profile",
        json=PUT
        | {
            "contact": {"name": "Jane Doe", "city": "Phnom Penh"},
            "experience": [work, "Previous role"],
            "education": [education],
            "awards": ["Engineering award"],
            "years_experience": 0.75,
        },
    )
    assert response.status_code == 200
    profile = (await client.get("/api/profile")).json()
    assert profile["contact"]["name"] == "Jane Doe"
    assert profile["contact"]["email"] == ""
    assert profile["experience"] == [work, "Previous role"]
    assert profile["education"] == [education]
    assert profile["awards"] == ["Engineering award"]
    assert profile["years_experience"] == 0.75
