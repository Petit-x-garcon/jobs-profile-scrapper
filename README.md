# Job Scraper

Personal job search tool: scrape job sites, filter by keywords, and rank jobs against your CV with AI.

- **Jobs**: fetch listings from DodoJob and Jobify, filter by keywords (`AI Engineer, Remote`), source and score.
- **Analyze with AI**: on request, score the jobs on screen against your latest CV/profile, with matching and missing skills. Results are reused until the profile or CV changes.
- **Profile & CV**: upload a PDF or DOCX CV; its text is extracted and turned into your profile. A new upload replaces the old CV and its profile data.
- **Site check**: test whether a URL is reachable, allowed by robots.txt, and has extractable content.

| Part | Stack | Where it runs |
|---|---|---|
| `backend/` | FastAPI, SQLAlchemy, Alembic, Python 3.13 (`uv`) | host |
| Celery worker (scraping) | same code as the backend | Docker |
| Postgres, Redis, pgAdmin | | Docker |
| `frontend/` | Next.js, React 19, shadcn/ui (npm) | host |

## Setup (once)

```bash
cp .env.example .env                   # repo root: Postgres/pgAdmin credentials
cp backend/.env.example backend/.env   # backend settings and Azure OpenAI keys
cp frontend/apps/web/.env.example frontend/apps/web/.env
```

Azure OpenAI keys are needed for **Analyze with AI** and **CV upload**. Without them the rest of the app works.

## Run

```bash
# 1. Infrastructure + worker (repo root)
docker compose up -d --build

# 2. Backend API (backend/)
uv sync
uv run alembic upgrade head
uv run fastapi dev app/main.py         # http://localhost:8000, docs at /docs

# 3. Frontend (frontend/)
npm install
npm run dev -w web                     # http://localhost:3000
```

pgAdmin: http://localhost:5050.

## Worker

The worker runs in Docker and has the code baked into its image. After changing backend code, rebuild it:

```bash
docker compose up -d --build worker
docker compose logs -f worker
```

To run it on the host instead (for debugging), stop the container first, then from `backend/`:

```bash
docker compose stop worker
uv run celery -A app.celery_app worker -l info --pool=solo
```

## Checks

```bash
# backend/
uv run ruff check . && uv run ruff format .
uv run pytest

# frontend/
npm run lint -w web && npm run typecheck -w web
```

## Notes

- No login: every endpoint is public and the app is single-user. Don't expose the API to the internet; it holds your CV.
- A successful site check does not mean the site permits ongoing scraping. Check its terms of service.
