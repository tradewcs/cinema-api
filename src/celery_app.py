from celery import Celery
from src.core.config import settings
from celery.schedules import crontab


celery_app = Celery(
    "cinema",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/1",
)

celery_app.autodiscover_tasks(["src.tasks"])

import src.tasks.cleanup_tokens

celery_app.conf.timezone = "UTC"

celery_app.conf.beat_schedule = {
    "delete-expired-tokens-every-hour": {
        "task": "delete_expired_tokens",
        "schedule": crontab(minute=0, hour="*"),
    },
}
