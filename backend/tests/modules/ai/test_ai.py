from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.ai import service
from app.modules.ai.service import AIBadResponse, AIUnavailable


def _client(content: str) -> MagicMock:
    msg = SimpleNamespace(message=SimpleNamespace(content=content))
    c = MagicMock()
    c.chat.completions.create = AsyncMock(return_value=SimpleNamespace(choices=[msg]))
    return c


async def test_enrich_parses_and_clamps():
    c = _client('{"summary": "- a\\n- b", "score": 150, "reasons": "ok"}')
    with patch.object(service, "_client", return_value=c):
        r = await service.enrich("x" * 10000, "profile")
    assert (r.score, r.reasons) == (100, "ok")
    sent = c.chat.completions.create.await_args.kwargs
    assert sent["response_format"] == {"type": "json_object"}
    assert len(sent["messages"][1]["content"]) < 6200


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


async def test_extract_profile_parses_cv():
    c = _client('{"headline": "Dev", "summary": "s", "skills": ["Go"], "years_experience": 3.6}')
    with patch.object(service, "_client", return_value=c):
        r = await service.extract_profile("cv " * 20000)
    assert (r.skills, r.years_experience, r.experience) == (["Go"], 4, [])
    assert len(c.chat.completions.create.await_args.kwargs["messages"][1]["content"]) == 20000
