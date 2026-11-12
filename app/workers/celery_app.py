from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery = Celery(
    "forwarder",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"],
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    beat_schedule={
        "process-queue-every-10s": {
            "task": "app.workers.tasks.process_queue",
            "schedule": 10.0,
        },
        "retry-unknown-every-5min": {
            "task": "app.workers.tasks.retry_unknown",
            "schedule": 300.0,
        },
        "backup-daily": {
            "task": "app.workers.tasks.run_backup",
            "schedule": crontab(hour=2, minute=0),
        },
    },
)
