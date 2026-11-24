# Agent rules

Monorepo: `backend/` (FastAPI) and `frontend/` (Next.js). These rules are for writing code.

Detailed rules per area live in `.claude/rules/`; see the "Topic rules" table in `backend/AGENTS.md` and `frontend/AGENTS.md`.

## General
- Keep it simple. Reuse existing code before writing new code.
- Small, focused files and functions. Split when a limit is passed.
- No secrets in code or logs. Never read or edit `.env`; document new settings in `.env.example`.

## Size limits
- Function: aim for 30 lines or less, split past 60. At most 5 parameters, 3 nesting levels (use early returns).
- File: aim for 300 lines or less, split past 500.
- Exception: generated shadcn files in `packages/ui`.

## Backend (`backend/`)
- FastAPI, Python 3.13, `uv`. Lint and format with `ruff`, test with `pytest`.
- SQLAlchemy (async) + Alembic + Postgres. Model change means generate a migration.
- Celery + Redis for background jobs (`tasks.py`).
- Modular monolith: `app/modules/<module>/` with `router.py`, `service.py`, `repository.py`, `models.py`, `schemas.py`. Create only the files needed.
- Flow: router -> service -> repository -> model. Routers hold no business logic.
- Other modules import only a module's `service.py` and `schemas.py`, never its repository or models.
- `app/core/` (settings, DB) and `app/shared/` (helpers) never import from `modules/`.
- Async everywhere (`async def`). Blocking calls go through `asyncio.to_thread`. Use `httpx.AsyncClient` with a timeout.
- Type hints on every parameter and return. Docstring on public functions.
- Raise custom exceptions, not `HTTPException`, in services. Errors return `{"detail": "<message>"}`.
- Settings only through `Settings` in `app/core/config.py`, no `os.getenv`. Use `logging`, never `print`.
- Add tests under `tests/modules/<module>/`.

## Frontend (`frontend/`)
- Next.js (App Router) + React 19, npm + Turborepo. Read `node_modules/next/dist/docs/` before using a Next.js API you are unsure of.
- **shadcn/ui first.** Use components from `packages/ui` (`@workspace/ui/components/<name>`). Missing one: `npx shadcn@latest add <name>`. Only then hand-write one in the same style.
- Tailwind CSS only, merged with `cn()`. Use theme tokens (`bg-background`, `text-muted-foreground`), no hard-coded colors. Flat colors, no gradients. Icons from `lucide-react`.
- Mobile-first and responsive. Support light and dark themes.
- Server components by default. `"use client"` only where needed, as low in the tree as possible.
- API calls through one axios client. Parse responses with zod. No `fetch` or axios inside components.
- Server state with TanStack Query, never fetch in `useEffect`. Shared client state with zustand.
- Strict TypeScript, no `any`. Use the `@/` alias. Files in kebab-case, components in PascalCase.
- Feature UI in `components/<feature>/`, shared UI in `components/shared/`.
- Run `npm run lint` and `npm run typecheck`; format changed files with Prettier.

## Backend <-> frontend contract
- Routes under `/api`. JSON fields `snake_case`, IDs are UUID strings, timestamps ISO 8601 UTC.
- Errors: `{"detail": "..."}`. Paginated lists use one shared shape, with 1-based `page` and `size`.
- Never return secrets. Expose `has_<field>: bool` instead.
- Changing a response means updating the backend schema and the frontend zod schema together.
