---
paths:
  - "tests/**"
---

# Tests

- pytest runs with `asyncio_mode = "auto"`: write `async def test_...` without `@pytest.mark.asyncio`.
- Tests mirror the modules: `tests/modules/<module>/test_service.py`, `test_router.py`. Multi-step flows across modules go in `tests/integration/`.
- No unit test touches a real database or network:
  - Mock the session with `MagicMock(spec=AsyncSession)`, using `AsyncMock` for `execute` / `commit`.
  - Patch external services, httpx, Redis and Celery.
- Patch a name where it is *used*, not where it is defined: `patch("app.modules.x.service._enqueue_job")`.
- `tests/conftest.py` holds autouse fixtures that set secrets and stub external side effects. Tests must not depend on `.env`.
- Cover the happy path and each error branch. Test a module through its `service.py` public functions, as other modules would call them.
- Run one file with `uv run pytest tests/modules/x/test_service.py`, and one test with `-k <name>`.
