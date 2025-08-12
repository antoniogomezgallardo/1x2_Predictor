from celery import Celery
from .config.settings import settings

celery_app = Celery(
    "quiniela_predictor",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["backend.app.services.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "backend.app.services.tasks.*": {"queue": "main-queue"},
    }
)

if __name__ == "__main__":
    celery_app.start()