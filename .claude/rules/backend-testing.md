---
paths:
  - "backend/tests/**"
---

# Backend: tests

- pytest with `asyncio_mode = "auto"`: write `async def test_...` with no marker.
- Tests mirror modules: `tests/modules/<module>/test_service.py`, `test_router.py`.
- No unit test touches a real database or network. Mock the session with `MagicMock(spec=AsyncSession)` and `AsyncMock`. Patch external services, httpx, Redis and Celery.
- Patch a name where it is used: `patch("app.modules.x.service._enqueue_job")`.
- Tests must not depend on `.env`; `tests/conftest.py` sets secrets and stubs side effects.
- Cover the happy path and each error branch. Test through the module's `service.py`.
- Run one file: `uv run pytest tests/modules/x/test_service.py`; one test: `-k <name>`.
