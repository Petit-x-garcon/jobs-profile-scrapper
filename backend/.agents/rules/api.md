---
paths:
  - "app/modules/**/router.py"
  - "app/modules/**/service.py"
  - "app/modules/**/schemas.py"
  - "app/modules/**/dependencies.py"
  - "app/modules/**/exceptions.py"
  - "app/shared/**"
  - "app/main.py"
---

# API layer: routers, services, schemas, errors

## Routers
- Keep handlers thin: the schema validates input, dependencies resolve the user and session, and one service call does the work.
- Declare `response_model=` and a matching return annotation. The docstring becomes the OpenAPI description: what the endpoint does, who may call it, and notable errors.
- Creates use `status_code=status.HTTP_201_CREATED`. Deletes return `Response(status_code=status.HTTP_204_NO_CONTENT)`.
- Lists return `PaginatedResponse[ItemSchema]` built with `shared/pagination.paginate_query` (`page`, `size`).
- Every endpoint declares its auth dependency explicitly. A public endpoint is deliberate and says so in its docstring.
- Each module's router is registered in `app/main.py` under the `/api` prefix.

## Services
- Default: a module of `async def` functions, imported as a module (`from app.modules.users import service as user_service`).
- Use a class only to wrap a stateful client (an HTTP client, a storage client). Build it once, in `lifespan` → `app.state` or as an `lru_cache` getter, and inject it with `Depends`.
- Pass `db: AsyncSession` as an argument; never store it on an object.
- Map ORM → response schema in the service (`Schema.model_validate(obj)` with `from_attributes=True`).
- Wrap third-party errors where you call them: `except httpx.HTTPError as exc: raise ExternalServiceException("...") from exc`.
- Services are the only code other modules call (see `architecture.md`).

## Schemas (Pydantic v2)
- Request models (`XxxCreate`, `XxxUpdate`) are separate from response models (`XxxResponse`), all in the module's `schemas.py`.
- Put input constraints in the schema (`Field(min_length=, max_length=, ge=)`, `Literal[...]`, `EmailStr`) so routers and services don't re-validate.
- Never return ORM instances or secret values. For a secret, expose `has_<field>: bool` instead.

## Error classes
`shared/exceptions.py` defines `AppException` and its common subclasses; the global handler maps each class to a status and returns `{"detail": message}`. Any other exception becomes a generic 500, and its traceback is logged.

| Exception | Status |
|---|---|
| `BadRequestException` | 400 |
| `UnauthorizedException` | 401 |
| `ForbiddenException` | 403 |
| `NotFoundException` | 404 |
| `ConflictException` | 409 |
| `ExternalServiceException` | 502 |

- Module-specific errors subclass these in the module's `exceptions.py`. For a status not listed, add a subclass and register it in the handler's status map.
- Don't raise `HTTPException` in services. It is acceptable in auth dependencies.
- Catch bare `Exception` only at a boundary that must turn any failure into a status (an SSE stream, a "test connection" action), and log it with `logger.exception`.

## Streaming (SSE)
- Finish auth and validation before returning `StreamingResponse`: the status code goes out with the first byte and can't change afterwards.
- Inside the generator, don't use the injected `get_db` session. Open one with `async_session_factory()`; the endpoint owns its sessions.
- Save state in `finally`, so a client disconnect still persists partial work.
