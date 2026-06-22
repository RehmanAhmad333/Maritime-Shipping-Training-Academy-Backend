from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "maritime_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.email_tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,  # 1 hour
)

# Beat Schedule
celery_app.conf.beat_schedule = {
    "send-weekly-digest": {
        "task": "app.tasks.email_tasks.send_weekly_digest",
        "schedule": crontab(day_of_week="monday", hour=9, minute=0),
    },
    "send-daily-digest": {
        "task": "app.tasks.email_tasks.send_daily_digest",
        "schedule": crontab(hour=9, minute=0),
    },
    "check-pending-emails": {
        "task": "app.tasks.email_tasks.retry_failed_emails",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
    },
}

if __name__ == "__main__":
    celery_app.start()