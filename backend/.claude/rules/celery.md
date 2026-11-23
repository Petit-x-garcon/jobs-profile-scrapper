---
paths:
  - "app/modules/**/tasks.py"
  - "app/worker.py"
---

# Background jobs (Celery)

Use Celery for work that is long, must survive a crash, or needs retries. Short post-response work (logging, notifications) uses FastAPI `BackgroundTasks`. Redis is the broker, and task results are not stored.

| Scenario | Tool |
|---|---|
| Blocking library call inside a request | `asyncio.to_thread` |
| Light post-response work | FastAPI `BackgroundTasks` |
| Long, retriable or crash-sensitive jobs | Celery |

- Tasks live in the owning module's `tasks.py` and are listed in `include=[...]` in `app/worker.py`.
- Celery is sync. The task function is a thin wrapper, `asyncio.run(_do_work(...))`, and the logic lives in async helpers that call the module's service.
- Never use the API's engine or `get_db` inside a task: asyncpg connections are bound to the event loop that opened them. Create a `NullPool` engine per run and dispose of it in `finally`; put that helper in `core/` once and reuse it.
- Task arguments are IDs only and must be JSON-serializable. Re-read the row inside the task, and handle "deleted while queued".
- Tasks must be idempotent: `acks_late` re-delivers a task after a worker crash, so it can run twice.
- Report progress in a DB status column, since there is no result backend.
- Separate the error types. A permanent error marks the row failed and is not retried; a transient one does `raise self.retry(countdown=...)` with backoff.
- Enqueue through a small service helper (`_enqueue_x`) so tests can patch it.
- Set the broker's visibility timeout above the slowest job, or Redis re-delivers it while it is still running.
- The worker doesn't auto-reload, so restart it after changing task code. On Windows, run it with `--pool=solo`.
