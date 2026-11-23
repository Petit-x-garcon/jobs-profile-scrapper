---
paths:
  - "backend/app/modules/**/models.py"
  - "backend/app/modules/**/repository.py"
  - "backend/app/core/database.py"
  - "backend/app/core/model_registry.py"
  - "backend/alembic/**"
---

# Backend: models, repositories, migrations

## Repositories
- One `repository.py` per module, `async def` functions with `db: AsyncSession` last. Query only this module's models.
- Return `None` for not found, unless the module already raises `NotFoundException`.
- Several writes that must succeed together: `flush()` as you go, commit once, in one function.
- Relationships use `lazy="selectin"` or `lazy="noload"`. Load extras with `selectinload(...)`; lazy loading raises `MissingGreenlet` in async code.

## Models
- SQLAlchemy 2.0 typed style: `Mapped[...]` + `mapped_column(...)`.
- UUID primary keys: `mapped_column(primary_key=True, default=uuid.uuid4)`.
- Timestamps are `DateTime(timezone=True)` with `datetime.now(timezone.utc)`. No `utcnow()`.
- Import every `models.py` in `app/core/model_registry.py`, or autogenerate misses it.

## Migrations
1. Change the model.
2. `uv run alembic revision --autogenerate -m "short description"`.
3. Read the file before applying. Any unintended `drop_table` / `drop_column` means stop. A rename shows as drop + add, so change it to `op.alter_column`.
4. A NOT NULL column on an existing table needs a `server_default` or backfill.
5. `uv run alembic upgrade head`, then `downgrade -1` and `upgrade head` again.
6. `uv run alembic heads` must show one head.

- One Alembic history for the whole monolith. Never edit a migration that already ran elsewhere.
