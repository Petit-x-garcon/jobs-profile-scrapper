---
paths:
  - "**/*.py"
---

# Python style

## Type hints
- Annotate every parameter and return value, including `-> None`.
- Use `X | None`, `list[str]`, `dict[str, int]`.
- Avoid `Any` and loose `dict`s for structured data; use a Pydantic model, dataclass or `TypedDict`.

## Naming
- Functions: verb + noun (`create_user`, `get_by_email`, `mark_failed`). Booleans: `is_` / `has_`. Private helpers: `_leading_underscore`.
- Inside a module the folder gives the context, so files are plain: `router.py`, `service.py`, `repository.py`, `models.py`, `schemas.py`.

## Docstrings and comments
- Every public function and class gets a docstring: one line on what it does or returns, then notable behavior (errors raised, side effects).
- Prefer self-documenting names. Comments explain *why* (a design choice, trade-off or constraint), never *what*. Keep them short.
- When you change code, update or delete the comments it makes stale.

## Size (guidelines, not hard limits)
- Function: aim for 5–30 lines; review past ~40; split past ~60. Each function has one reason to change.
- At most 5 parameters; group more into a schema or dataclass. At most 2–3 nesting levels; prefer early returns.
- File: review past ~300 lines; split past ~500 when it mixes responsibilities (see `architecture.md`).
- Split when that makes code easier to read, reuse or test, not to hit a number.
