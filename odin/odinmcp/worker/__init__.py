from celery import Celery
from odinmcp.config import settings

odin_worker = Celery(
    "OdinWorker",
    broker=settings.celery_broker,
    backend=settings.celery_backend,
)
