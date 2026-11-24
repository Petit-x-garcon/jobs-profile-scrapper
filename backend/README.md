# Job Scraper backend

FastAPI + Celery + Postgres + Redis. Python 3.13, managed with `uv`.

## Run

```bash
# 1. backend/.env: copy backend/.env.example and fill values (Azure keys optional)
# 2. infra + Celery worker (repo root): copy .env.example to .env first
docker compose up -d --build

# 3. migrate and run the API
cd backend
uv sync
uv run alembic upgrade head
uv run fastapi dev app/main.py   # http://localhost:8000, docs at /docs
```

The worker runs in Docker and only scrapes; it reaches Postgres and Redis by service
name, so `DATABASE_URL`/`REDIS_URL` there are overridden. Code is baked into the image:
after changing backend code, run `docker compose up -d --build worker`.
Logs: `docker compose logs -f worker`.

Azure OpenAI keys (`backend/.env`) are used by the API for "Analyze with AI" and CV
upload. Without them the rest of the app works and those two return a clear error.
pgAdmin: http://localhost:5050.

## Checks

```bash
uv run ruff check . && uv run ruff format .
uv run pytest
```
