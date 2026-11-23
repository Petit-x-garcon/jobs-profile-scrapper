# Architecture: modular monolith

One deployable (FastAPI API + Celery worker, one Postgres database), split into **business modules** with clear boundaries. A module is a business capability (`users`, `auth`, `billing`), not a technical layer. This file has no `paths:` filter, so it loads for every backend task.

## Layout

```
app/
├── main.py            # app factory, lifespan, include_router for each module
├── worker.py          # Celery app; lists each module's tasks in include=[...]
├── core/              # infrastructure: settings, DB engine, security/JWT, Redis, logging
├── shared/            # code several modules use: base exceptions + handlers, pagination, utils
└── modules/
    └── <module>/
        ├── __init__.py       # empty
        ├── router.py         # HTTP endpoints
        ├── service.py        # business rules; the module's public API
        ├── repository.py     # queries for this module's models
        ├── models.py         # SQLAlchemy models
        ├── schemas.py        # Pydantic request/response models (also public)
        ├── exceptions.py     # module-specific AppException subclasses
        ├── dependencies.py   # Depends callables for this module
        └── tasks.py          # Celery tasks (only if the module needs them)
tests/modules/<module>/     # tests mirror the module
```

Create only the files a module needs. Inside a module the flow is **router → service → repository → model**; see `api.md` and `database.md` for what each file may contain.

## Boundaries
- **Public surface of a module:** `service.py` functions and `schemas.py` types. Other modules import only these.
- Never import another module's `repository`, `models` or a `_private` function. If you need its data, add or call a service function.
- Dependencies point one way. If module A and B need each other, move the shared part to a third module or to `shared/`, or pass data in as arguments. No import cycles.
- Across modules, store the other module's id as a plain column (a FK to its table is fine). No ORM `relationship()` across modules.
- A cross-module operation that must be atomic takes the caller's `db: AsyncSession` and doesn't commit on its own; the outermost service commits once.
- `core/` and `shared/` never import from `modules/`.
- `shared/` holds technical helpers only. If it contains business rules, it is really a module.

## Adding a module
1. Create `app/modules/<name>/` with the files you need and an empty `__init__.py`.
2. Register the router in `app/main.py`: `app.include_router(x_router, prefix="/api")`.
3. Import its `models.py` in `app/core/model_registry.py` (Alembic reads that file), then autogenerate the migration (see `database.md`).
4. If it has tasks, add `app.modules.<name>.tasks` to `include=[...]` in `app/worker.py`.
5. Add `tests/modules/<name>/`.

## Size and splitting
- A module that grows past ~10 files or mixes two capabilities is split into two modules.
- A single file past ~500 lines becomes a package (`service/` with an empty `__init__.py`, a main `core.py` plus focused siblings). Keep callers importing `from app.modules.x import service as x_service`.
