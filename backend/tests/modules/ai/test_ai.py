from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.ai import service
from app.modules.ai.service import AIBadResponse, AIUnavailable


def _client(content: str) -> MagicMock:
    c = MagicMock()
    c.__aenter__.return_value = c
    c.responses.create = AsyncMock(return_value=SimpleNamespace(output_text=content))
    return c


async def test_enrich_parses_and_clamps():
    c = _client('{"summary": "- a\\n- b", "score": 150, "reasons": "ok"}')
    with patch.object(service, "_client", return_value=c):
        r = await service.enrich("x" * 10000, "profile")
    assert (r.score, r.reasons) == (100, "ok")
    sent = c.responses.create.await_args.kwargs
    assert sent["text"] == {"format": {"type": "json_object"}}
    assert sent["store"] is False
    instructions, user = sent["input"]
    assert instructions["role"] == "system"
    assert "json" in instructions["content"].lower()
    assert user["role"] == "user"
    assert len(user["content"]) < 6200


async def test_negative_score_clamped():
    c = _client('{"summary": "s", "score": -5, "reasons": "r"}')
    with patch.object(service, "_client", return_value=c):
        assert (await service.enrich("j", "p")).score == 0


async def test_invalid_json_raises():
    with patch.object(service, "_client", return_value=_client("nope")):
        with pytest.raises(AIBadResponse):
            await service.enrich("j", "p")


async def test_unconfigured_raises(monkeypatch):
    monkeypatch.setattr(service.settings, "azure_openai_endpoint", None)
    with pytest.raises(AIUnavailable):
        await service.enrich("j", "p")


@pytest.mark.parametrize("suffix", ["", "/openai/v1", "/openai/v1/"])
async def test_client_uses_v1_base_url(monkeypatch, suffix):
    resource_url = "https://example.services.ai.azure.com"
    monkeypatch.setattr(service.settings, "azure_openai_endpoint", resource_url + suffix)
    monkeypatch.setattr(service.settings, "azure_openai_api_key", "test-key")
    monkeypatch.setattr(service.settings, "azure_openai_deployment", "gpt-5-mini")
    async with service._client() as client:
        assert str(client.base_url) == resource_url + "/openai/v1/"


async def test_extract_profile_parses_cv():
    c = _client(
        '{"headline":"Dev","summary":"s","skills":["Go"],"years_experience":0.75,'
        '"experience":[{"title":"Developer","dates":"9 months"},{"title":"Intern"}],'
        '"education":[{"degree":"Data Science","university":"Example University"}]}'
    )
    with patch.object(service, "_client", return_value=c):
        r = await service.extract_profile("cv " * 20000)
    assert (r.skills, r.years_experience) == (["Go"], 0.75)
    assert r.model_dump()["experience"][1]["title"] == "Intern"
    assert r.model_dump()["education"][0]["year"] == ""
    instructions, user = c.responses.create.await_args.kwargs["input"]
    assert "json" in instructions["content"].lower()
    assert len(user["content"]) == 20000
