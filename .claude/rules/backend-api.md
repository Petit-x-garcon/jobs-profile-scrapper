---
paths:
  - "backend/app/modules/**/router.py"
  - "backend/app/modules/**/service.py"
  - "backend/app/modules/**/schemas.py"
  - "backend/app/modules/**/dependencies.py"
  - "backend/app/modules/**/exceptions.py"
  - "backend/app/shared/**"
  - "backend/app/main.py"
---

# Backend: routers, services, schemas, errors

## Routers
- Thin handlers: schema validates input, dependencies resolve user and session, one service call does the work.
- Set `response_model=`. Create returns 201, delete returns 204.
- Lists return `PaginatedResponse[Item]` via `shared/pagination.paginate_query` (`page`, `size`).
- Every endpoint declares its auth dependency. A public endpoint is deliberate and says so in its docstring.

## Services
- Module of `async def` functions, imported as `from app.modules.users import service as user_service`.
- Use a class only for a stateful client (HTTP, storage). Build it once and inject with `Depends`.
- Take `db: AsyncSession` as an argument, never store it.
- Map ORM to response schema in the service (`Schema.model_validate(obj)`).
- Wrap third-party errors: `except httpx.HTTPError as exc: raise ExternalServiceException("...") from exc`.

## Schemas (Pydantic v2)
- Separate `XxxCreate`, `XxxUpdate`, `XxxResponse` in `schemas.py`.
- Put input constraints in the schema (`Field(min_length=...)`, `Literal`, `EmailStr`).
- Never return ORM instances or secrets. Expose `has_<field>: bool`.

## Errors
Raise `AppException` subclasses from `shared/exceptions.py`. The global handler returns `{"detail": message}`.

| Exception | Status |
|---|---|
| `BadRequestException` | 400 |
| `UnauthorizedException` | 401 |
| `ForbiddenException` | 403 |
| `NotFoundException` | 404 |
| `ConflictException` | 409 |
| `ExternalServiceException` | 502 |

- Module errors subclass these in `exceptions.py`. Add a subclass if no status fits.
- No `HTTPException` in services. Messages tell the user what to do next, with no SQL or stack traces.
- Catch bare `Exception` only at a boundary, and use `logger.exception`.
