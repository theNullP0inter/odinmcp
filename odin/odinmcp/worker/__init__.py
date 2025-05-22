
from odinmcp.config import settings
from celery import Celery, shared_task
from celery.contrib.abortable import AbortableTask


odin_worker = Celery(
    "OdinWorker",
    broker=settings.celery_broker,
    backend=settings.celery_backend
)



@odin_worker.task(name="test_task",base=AbortableTask, bind=True, queue="test_queue")
def test_task(
    self,
) -> None:
    print("test_task")



