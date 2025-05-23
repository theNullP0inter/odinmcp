from typing import Any, Type
from mcp.server.lowlevel.server import Server as MCPServer
from celery import Celery
from odinmcp.config import settings
from mcp.types import JSONRPCRequest
from odinmcp.models.auth import CurrentUser
import json

class OdinWorker:

    def __init__(self, mcp_server: MCPServer, current_user_model: Type[CurrentUser]):
        self.mcp_server = mcp_server
        self.current_user_model = current_user_model
        self.worker = self.build_worker()

    def get_worker(self):
        return self.worker

    
    def send_handle_mcp_request(self, request: JSONRPCRequest, channel_id: str, current_user: CurrentUser):
        self.worker.send_task("odinmcp.handle_mcp_request", args=(request.model_dump_json(by_alias=True, exclude_none=True), channel_id, current_user.model_dump_json(by_alias=True, exclude_none=True)))
        

    def build_worker(self):
        worker =  Celery(
            self.mcp_server.name,
            broker=settings.celery_broker,
            backend=settings.celery_backend
        )
        worker.task(self.handle_mcp_request, name="odinmcp.handle_mcp_request")
        return worker

    def handle_mcp_request(self, request: str, channel_id: str, current_user: str) -> None:
        
        request = JSONRPCRequest.model_validate_json(request)
        current_user = self.current_user_model.model_validate_json(current_user)

        # TODO: handle mcp request

        
        

    

    
        