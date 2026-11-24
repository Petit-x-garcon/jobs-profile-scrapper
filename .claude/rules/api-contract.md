---
paths:
  - "backend/app/**/*.py"
  - "frontend/apps/web/lib/**"
---

# API contract (backend <-> frontend)

- The browser calls the backend directly at `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`) through the axios client in `lib/api/client.ts`. Every backend route is under `/api`; CORS origins are set in backend `Settings`.
- No auth yet.
- JSON fields are `snake_case`. IDs are UUID strings. Timestamps are ISO 8601 UTC.
- Errors: `{"detail": "<message>"}`. Validation errors (422) send `detail` as a list of `{msg, ...}`.
- Lists: `{items: [...], total, page, size}` with 1-based `page`. Backend: `Page[T]` in `app/shared/pagination.py`. Frontend: the matching zod schema in `lib/api/schemas.ts` (e.g. `jobPageSchema`).
- Secrets are never returned; expose `has_<field>: bool`.
- Changing a response means changing the backend schema and the frontend zod schema in the same change. Adding a field is safe; renaming or removing needs both sides updated.
