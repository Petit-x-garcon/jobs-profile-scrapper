---
paths:
  - "backend/app/**/*.py"
---

# Backend: modular monolith

```
app/
├── main.py       # app factory, include_router per module
├── celery_app.py # Celery app, includes app.tasks
├── tasks.py      # Celery tasks (call module services)
├── core/         # settings, DB engine, security, logging
├── shared/       # technical helpers: base exceptions, pagination, utils
└── modules/<module>/
    ├── router.py  service.py  repository.py  models.py  schemas.py
    ├── exceptions.py  dependencies.py   # only if needed
tests/modules/<module>/
```

- Flow: router -> service -> repository -> model.
- Other modules import only `service.py` and `schemas.py`. Never another module's repository, models or `_private` function.
- Dependencies point one way, no import cycles. Shared part goes to a third module or `shared/`.
- No ORM `relationship()` across modules. Store the other module's id as a plain column.
- A cross-module operation that must be atomic takes the caller's `db` and does not commit; the outermost service commits once.
- `core/` and `shared/` never import from `modules/`. `shared/` has no business rules.
- New module: create `app/modules/<name>/`, register its router in `main.py` with the `/api` prefix, import its `models.py` in `app/core/model_registry.py`, add its tasks to `app/tasks.py`, add tests.
- A module past ~10 files, or mixing two capabilities, is split. A file past ~500 lines becomes a package.

## Python style
- Type hints on every parameter and return (`X | None`, `list[str]`). No `Any`; use Pydantic, dataclass or `TypedDict`.
- Names: functions are verb + noun (`create_user`), booleans `is_` / `has_`, private helpers `_name`.
- Public functions and classes get a one-line docstring. Comments explain why, not what.
- Async: no `requests` or `time.sleep`. Never share one `AsyncSession` across `asyncio.gather`.
- Logging: `logger = logging.getLogger(__name__)`, %-style args, never log secrets.
