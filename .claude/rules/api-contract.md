---
paths:
  - "backend/app/**/*.py"
  - "frontend/apps/web/lib/**"
---

# API contract (backend <-> frontend)

- The browser calls relative `/api/...`; a Next.js route handler proxies to `BACKEND_URL` (default `http://localhost:8000`). Every backend route is under `/api`. Trailing slashes are significant.
- Auth: `Authorization: Bearer <access_token>`. The refresh token is an httpOnly cookie. The frontend's copy of the role is for display only.
- JSON fields are `snake_case`. IDs are UUID strings. Timestamps are ISO 8601 UTC.
- Errors: `{"detail": "<message>"}`. Validation errors (422) send `detail` as a list of `{msg, ...}`.
- Lists: `{number, size, total_elements, total_pages, first, last, has_next, has_previous, data: [...]}` with 1-based `page` and `size`. Backend: `PaginatedResponse[T]` in `app/shared/pagination.py`. Frontend: `paginated(itemSchema)` in `lib/schemas.ts`.
- Secrets are never returned; expose `has_<field>: bool`.
- Changing a response means changing the backend schema and the frontend zod schema in the same change. Adding a field is safe; renaming or removing needs both sides updated.
