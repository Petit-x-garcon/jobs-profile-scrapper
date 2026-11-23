from celery import Celery

from app.core.config import settings

celery_app = Celery("jobs", broker=settings.redis_url, include=["app.tasks"])
celery_app.conf.task_acks_late = True
