from mcp.server.lowlevel.server import Server as MCPServer
from celery import Celery
from odinmcp.config import settings

class OdinWorker:

    def __init__(self, mcp_server: MCPServer):
        self.mcp_server = mcp_server

    def build(self):
        worker =  Celery(
            self.mcp_server.name,
            broker=settings.celery_broker,
            backend=settings.celery_backend
        )
        worker.task(self.test_task)
        return worker

    def test_task(self, a, b):
        return a + b

    

    
        