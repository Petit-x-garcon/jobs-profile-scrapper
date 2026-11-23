---
paths:
  - "app/modules/**/models.py"
  - "app/modules/**/repository.py"
  - "app/core/database.py"
  - "app/core/model_registry.py"
  - "alembic/**"
---

# Database: repositories, models, migrations

## Repositories
- One `repository.py` per module, made of `async def` functions with `db: AsyncSession` last: `get_by_email(email, db)`. It queries only that module's models.
- Return `None` for "not found" unless the module already raises `NotFoundException`; match the module.
- Write functions commit, so each call is its own transaction. When several writes must succeed or fail together, put them in one function that `flush()`es as it goes and commits once. Calling several committing functions in a row is not atomic.
- Relationships are `lazy="selectin"` or `lazy="noload"`. Lazy loading in async code raises `MissingGreenlet`, so load what you need with `.options(selectinload(...))`.
- Paginate with `shared/pagination.paginate_query(db, stmt, page, size)`.

## Models
- Use the SQLAlchemy 2.0 typed style: `Mapped[...]` + `mapped_column(...)`.
- Primary keys are native UUIDs: `Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)`.
- Timestamps are `DateTime(timezone=True)` with `default=lambda: datetime.now(timezone.utc)`. Never use naive `datetime.utcnow()`.
- No `relationship()` between models of different modules (see `architecture.md`).
- Import every module's `models.py` in `app/core/model_registry.py`, or autogenerate won't see it. `alembic/env.py` imports that file; don't remove the import, or autogenerate writes a migration that drops every table.

## Migrations: generate them, don't hand-write them
1. Change the model.
2. `uv run alembic revision --autogenerate -m "short description"`.
3. Read the generated file and fix it before applying:
   - Any `drop_table` / `drop_column` you didn't intend means stop. A rename shows up as drop + add, which loses data; change it to `op.alter_column(..., new_column_name=...)`.
   - Autogenerate doesn't detect CHECK constraints, renames, enum value changes or some `server_default` changes. Add those by hand in the same file.
   - A NOT NULL column on an existing table needs a `server_default` or a backfill step.
   - `downgrade()` must exactly reverse `upgrade()`.
4. `uv run alembic upgrade head`, then `downgrade -1` and `upgrade head` again to prove the downgrade works.
5. `uv run alembic heads` must print exactly one head.

- One Alembic history for the whole monolith (`backend/alembic/`), not one per module.
- Never edit a migration that has run anywhere else; add a new one.
- A data-only migration may use `alembic revision -m "..."` without `--autogenerate`.
