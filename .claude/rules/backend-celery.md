---
paths:
  - "backend/app/tasks.py"
  - "backend/app/celery_app.py"
---

# Backend: background jobs (Celery + Redis)

Use Celery for work that is long, must survive a crash, or needs retries. Short post-response work uses FastAPI `BackgroundTasks`. A blocking call inside a request uses `asyncio.to_thread`.

- Tasks live in `app/tasks.py`, which `app/celery_app.py` lists in `include=[...]`.
- Celery is sync: the task is a thin `asyncio.run(_do_work(...))` wrapper, and the logic is in async helpers that call the module's service.
- Never reuse the API's engine or `get_db` in a task. Create a `NullPool` engine per run and dispose of it in `finally`.
- Task arguments are JSON-serializable IDs only. Re-read the row in the task and handle "deleted while queued".
- Tasks are idempotent; they can run twice after a worker crash.
- No result backend: report progress in a DB status column.
- A permanent error marks the row failed. A transient error does `raise self.retry(countdown=...)` with backoff.
- Enqueue through a small helper (`_enqueue_x`) so tests can patch it.
- The worker does not auto-reload. On Windows run it with `--pool=solo`.
