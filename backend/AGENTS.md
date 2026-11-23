# Backend (FastAPI): agent instructions

FastAPI API and Celery worker for Job Scraper, built as a modular monolith. Python 3.13, managed with `uv`. This file is the main source of instructions: `CLAUDE.md` imports it, and the topic rules below fill in the details.

## Topic rules

They live in `.claude/rules/` (the only copy), which Claude Code loads automatically. Read the matching file before changing that area:

| File | Applies to | Covers |
|---|---|---|
| `backend-architecture.md` | all backend code | Modular monolith: folder layout, module boundaries, adding a module |
| `api-contract.md` | all backend code | URLs, auth header, error shape, pagination, SSE frames shared with the frontend |
| `backend-api.md` | `router`, `service`, `schemas`, `dependencies`, `exceptions` files, `app/shared` | Routers, services, schemas, error classes, SSE |
| `backend-database.md` | `models`, `repository` files, `alembic/` | Models, repositories, transactions, migrations |
| `backend-celery.md` | `app/tasks.py`, `app/celery_app.py` | Background jobs |
| `backend-testing.md` | `tests/` | Test layout, mocking, fixtures |


## Commands

Run from `backend/`. `docker compose up -d` (repo root) starts the infrastructure (Postgres, pgAdmin, Redis); the API and worker run on the host.

```bash
uv sync                                                # install dependencies
uv run uvicorn app.main:app --reload                   # API :8000, docs at /docs
uv run celery -A app.worker.celery_app worker -l info --pool=solo
#   --pool=solo: the default prefork pool doesn't run on Windows. No auto-reload: restart after task changes.

uv run ruff check --fix                                # lint + sort imports (run from backend/)
uv run ruff format                                     # code layout; run after `check --fix`
uv run ty check                                        # type check
uv run pytest -q                                       # full suite
uv run pytest tests/modules/x/test_service.py -k save # one file / one test

uv run alembic revision --autogenerate -m "add status to users"
uv run alembic upgrade head                            # `downgrade -1` rolls back one
uv run alembic check                                   # fails if models and DB differ
```

Dev tools (ruff, ty, pytest, alembic, celery) must be listed in `pyproject.toml` before these commands work; add them when the first module needs them.

## Definition of done

1. `uv run ruff check` and `uv run ruff format --check` both pass.
2. `ty check` reports no new diagnostics in the files you touched.
3. Tests are added or updated, and `pytest` passes.
4. Model changed → migration generated, reviewed and applied (see `database.md`).
5. New setting → added to `Settings` and documented in `.env.example`.
6. Response shape changed → the frontend zod schema is updated too (see `api-contract.md`).

## Architecture in one paragraph

Code is grouped by business module under `app/modules/<module>/`, not by technical layer. Inside a module the flow is router → service → repository → model. Other modules may call only a module's `service.py` and `schemas.py`. Infrastructure lives in `app/core/`, cross-module technical helpers in `app/shared/`. Details and the new-module checklist are in `architecture.md`.

## Rules for every file

**Async**
- Routes, services and repositories are `async def`.
- Blocking calls go through `await asyncio.to_thread(...)`: file parsing, hashing large files, SMTP, sync SDK clients.
- HTTP uses `httpx.AsyncClient` with a timeout. No `requests` or `time.sleep` in `app/`.
- Never share one `AsyncSession` between concurrent coroutines (`asyncio.gather`).

**Auth**
- Every endpoint declares its auth dependency explicitly; a public endpoint is deliberate and documented.
- Role and permission checks go through shared dependencies, never inline string comparisons.

**Errors**
- Raise `AppException` subclasses. The global handler returns `{"detail": "<message>"}` with the mapped status; the frontend reads `detail`.
- Don't raise `HTTPException` in services. If no class fits the status you need, add one (see `backend-api.md`).
- Messages are shown to users: say what to do next, and never include secrets, SQL or stack traces.

**Config and secrets**
- Every setting lives in `Settings` (`app/core/config.py`) and is read via `settings`. No `os.getenv` in `app/`.
- Never edit or print `.env`: it holds real credentials. Document new settings in `.env.example`.
- Encrypt stored secrets; never log or return them.
- Before the server fetches a URL a user supplied, validate it against SSRF (block private and loopback addresses).

**Logging**
- Each module defines `logger = logging.getLogger(__name__)`. Never use `print()`.
- Use %-style arguments and include IDs: `logger.info("Saved user '%s'", user_id)`.
- Never log passwords, tokens, API keys or OTP codes.
