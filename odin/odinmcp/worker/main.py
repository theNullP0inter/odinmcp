from typing import Any, Type
from datetime import timedelta
from mcp.types import (
    ClientRequest, ServerRequest, ClientNotification, ServerNotification, ClientResult, ServerResult
)
from mcp.shared.session import (
    SendRequestT, SendResultT, SendNotificationT, ReceiveResultT, ProgressFnT
)
from mcp.shared.message import MessageMetadata, SessionMessage
from mcp.server.lowlevel.server import Server as MCPServer
from celery import Celery
from odinmcp.config import settings
from mcp.types import JSONRPCRequest
from odinmcp.models.auth import CurrentUser
import json
from mcp.client.session import ClientSession
from asgiref.sync import async_to_sync
from contextlib import AbstractAsyncContextManager, AsyncExitStack, asynccontextmanager
from mcp.server.lowlevel.server import Server as MCPServer
from mcp.server.session import ServerSession
from mcp.server.lowlevel.server import LifespanResultT, request_ctx
from mcp.server.models import InitializationOptions
from mcp.types import ErrorData
from odinmcp.session import OdinSession
from mcp.shared.context import RequestContext
from mcp.shared.exceptions import McpError

class OdinWorker:

    def __init__(
        self, 
        mcp_server: MCPServer, 
        current_user_model: Type[CurrentUser],
    ):
        self.mcp_server = mcp_server
        self.current_user_model = current_user_model
        self.worker = self._build_worker()

    def get_worker(self):
        return self.worker

    
    def send_handle_mcp_request(self, request: JSONRPCRequest, channel_id: str, current_user: CurrentUser):
        self.worker.send_task("odinmcp.handle_mcp_request", args=(request.model_dump_json(by_alias=True, exclude_none=True), channel_id, current_user.model_dump_json(by_alias=True, exclude_none=True)))
        

    def _build_worker(self):
        worker =  Celery(
            self.mcp_server.name,
            broker=settings.celery_broker,
            backend=settings.celery_backend
        )
        worker.task(self.task_handle_mcp_request, name="odinmcp.handle_mcp_request")
        return worker

    def task_handle_mcp_request(self, request: str, channel_id: str, current_user: str) -> None:
        return async_to_sync(self.task_async_handle_mcp_request)(request, channel_id, current_user)

    async def task_async_handle_mcp_request(self, request: str, channel_id: str, current_user: str) -> None:
        
        
        current_user = self.current_user_model.model_validate_json(current_user)
        

        print("self.mcp_server.request_handlers: ", self.mcp_server.request_handlers)
        
        # Option 3: replicate _handle_request & create custom session
        async with AsyncExitStack() as stack:
            lifespan_context = await stack.enter_async_context(self.mcp_server.lifespan(self.mcp_server))
            session = OdinSession(
                channel_id,
                current_user,
                self.mcp_server.create_initialization_options(),
            )
            rpc_request = JSONRPCRequest.model_validate_json(request)
            cli_req = ClientRequest(json.loads(request))

            if type(cli_req.root) in self.mcp_server.request_handlers:
                handler = self.mcp_server.request_handlers[type(cli_req.root)]
                token = None
                try:
                    token = request_ctx.set(
                        RequestContext(
                            rpc_request.id,
                            rpc_request.params.get("_meta", None),
                            session, 
                            lifespan_context,
                        )
                    ) 
                    response = await handler(cli_req.root)
                    print("response success: ", response)
                except McpError as err:
                    response = err.error
                    print("response mcp error: ", response)
                except Exception as err:
                    response = ErrorData(code=0, message=str(err), data=None)
                    print("response error: ", response)
                finally:
                    # Reset the global state after we are done
                    if token is not None:
                        request_ctx.reset(token)
                
                # TODO[Later]: send and event to Hermod using channel_id
            else:
                # TODO[Later]: send and error event to Hermod using channel_id
                print(f"Handler not found for request type: {type(cli_req.root)}")



    
        