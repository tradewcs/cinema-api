from celery import Celery
from src.core.config import settings
from celery.schedules import crontab


celery_app = Celery(
    "cinema",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/1",
)

celery_app.autodiscover_tasks(["src.tasks"])



celery_app.conf.beat_schedule = { }