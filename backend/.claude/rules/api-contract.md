# API contract (backend ↔ frontend)

The same file lives in the `backend/` and `frontend/` rule folders. Change both together.

## Transport
- The browser calls relative `/api/...` URLs. A Next.js route handler (`frontend/apps/web/app/api/[...path]/route.ts`) proxies them to `BACKEND_URL` (default `http://localhost:8000`). Every backend route is mounted under `/api`.
- Route handlers can't proxy WebSockets; if one is needed, rewrite it to the backend in `next.config.ts`.
- Trailing slashes are significant and preserved.
- Keep response compression off for streaming (SSE) routes so events aren't buffered.

## Auth
- Requests send `Authorization: Bearer <access_token>`. The refresh token is an httpOnly cookie.
- The frontend's copy of the user's role is for display only, never for access control.

## Data shapes
- JSON field names are `snake_case` on both sides. IDs are UUID strings; timestamps are ISO 8601 in UTC.
- **Errors:** `{"detail": "<message for the user>"}` with an HTTP status. FastAPI validation errors (422) send `detail` as a list of `{msg, ...}`. The frontend reads all of these with `errorMessage()` in `lib/api/client.ts`.
- **Lists:** paginated endpoints return `{number, size, total_elements, total_pages, first, last, has_next, has_previous, data: [...]}`. That is `PaginatedResponse[T]` in `backend/app/shared/pagination.py`, and `paginated(itemSchema)` in `frontend/apps/web/lib/schemas.ts`. Pages are 1-based (`page`, `size` query params).
- **Secrets** are never returned. The API exposes `has_<field>: bool` instead.

## Server-sent events
Each frame is exactly `data: {json}\n\n`, with a `type` field that discriminates the frame (for example `token`, `done`, `error`). Auth and validation failures happen before the stream starts, so they arrive as a normal HTTP error, not as a frame.

## Changing the contract
- Change the backend response schema and the frontend zod schema (`lib/api/<resource>.ts`) in the same change. The frontend `.parse()`s every response, so a mismatch throws at runtime.
- Adding a field is safe. Renaming or removing one needs both sides updated before either is deployed.
