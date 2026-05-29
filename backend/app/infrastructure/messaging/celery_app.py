from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "blood-helper",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.application.tasks.forecasting",
        "app.application.tasks.inventory",
        "app.application.tasks.campaigns",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "run-daily-forecasts": {
            "task": "app.application.tasks.forecasting.run_all_forecasts",
            "schedule": crontab(hour=2, minute=0),
        },
        "check-expiring-inventory": {
            "task": "app.application.tasks.inventory.check_expiring_blood_units",
            "schedule": crontab(hour=7, minute=0),
        },
        "check-critical-inventory": {
            "task": "app.application.tasks.inventory.check_critical_levels",
            "schedule": crontab(minute="*/30"),
        },
    },
)
