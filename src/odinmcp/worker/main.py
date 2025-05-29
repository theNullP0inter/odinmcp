import hashlib
from typing import Any, Type, Union
from datetime import timedelta
from celery.result import AsyncResult
from mcp.types import (
    CancelledNotification, ClientRequest, ProgressNotification, ServerRequest, ClientNotification, ServerNotification, ClientResult, ServerResult
)
from mcp.shared.session import (
    SendRequestT, SendResultT, SendNotificationT, ReceiveResultT, ProgressFnT
)
from mcp.shared.message import MessageMetadata, SessionMessage
from mcp.server.lowlevel.server import Server as MCPServer
from celery import Celery, states
from odinmcp.constants import MCP_CELERY_PROGRESS_STATE
from odinmcp.config import settings
from mcp.types import JSONRPCRequest, JSONRPCNotification, JSONRPCResponse, JSONRPCError
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
from odinmcp.worker.session import OdinWorkerSession
from mcp.shared.context import RequestContext
from mcp.shared.exceptions import McpError
# from celery.task.control import revoke

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

    
    def handle_mcp_request(self, request: JSONRPCRequest, channel_id: str, current_user: CurrentUser):
        self.worker.send_task(
            "handle_mcp_request", 
            args=(request.model_dump_json(by_alias=True, exclude_none=True), channel_id, current_user.model_dump_json(by_alias=True, exclude_none=True))
        )
    
    def handle_mcp_notification(self, notification: JSONRPCNotification, channel_id: str, current_user: CurrentUser):
        self.worker.send_task("handle_mcp_notification", args=(notification.model_dump_json(by_alias=True, exclude_none=True), channel_id, current_user.model_dump_json(by_alias=True, exclude_none=True)))
    
    def handle_mcp_response(self, response: Union[JSONRPCResponse, JSONRPCError], channel_id: str, current_user: CurrentUser):
        self.worker.send_task(
            "handle_mcp_response", 
            args=(response.model_dump_json(by_alias=True, exclude_none=True), channel_id, current_user.model_dump_json(by_alias=True, exclude_none=True)),
            task_id=self._generate_response_task_id(response.id, current_user, channel_id)
        )

    def terminate_session(self, channel_id: str, current_user: CurrentUser):
        self.worker.send_task(
            "terminate_session", 
            args=(channel_id, current_user.model_dump_json(by_alias=True, exclude_none=True))
        )

    def _build_worker(self):
        worker =  Celery(
            self.mcp_server.name,
            broker=settings.celery_broker,
            backend=settings.celery_backend
        )
        worker.task(self.task_handle_mcp_request, name="handle_mcp_request")
        worker.task(self.task_handle_mcp_notification, name="handle_mcp_notification")
        worker.task(self.task_handle_mcp_response, name="handle_mcp_response")
        worker.task(self.task_terminate_session, name="terminate_session")
        return worker

    def _generate_response_task_id(self, request_id: str, current_user: CurrentUser, channel_id: str) -> str:
        return hashlib.sha256(f"response_{current_user.user_id}_{channel_id}_{request_id}".encode()).hexdigest()

    def task_handle_mcp_request(self, request: str, channel_id: str, current_user: str) -> None:
        return async_to_sync(self.task_async_handle_mcp_request)(request, channel_id, current_user)

    async def task_async_handle_mcp_request(self, request: str, channel_id: str, current_user: str) -> None:

        current_user = self.current_user_model.model_validate_json(current_user)
        async with AsyncExitStack() as stack:
            lifespan_context = await stack.enter_async_context(self.mcp_server.lifespan(self.mcp_server))
            session = OdinWorkerSession(
                channel_id,
                current_user,
                self.mcp_server.create_initialization_options(),
                response_task_id_generator=self._generate_response_task_id,
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
                except McpError as err:
                    response = err.error
                except Exception as err:
                    response = ErrorData(code=0, message=str(err), data=None)
                finally:
                    # Reset the global state after we are done
                    if token is not None:
                        request_ctx.reset(token)
                
                
            else:
                response = ErrorData(code=0, message="Handler not found", data=None)

            await session._send_response(response, rpc_request.id)
   
    def task_handle_mcp_notification(self, notification: str, channel_id: str, current_user: str) -> None:
        return async_to_sync(self.task_async_handle_mcp_notification)(notification, channel_id, current_user)
    
    async def task_async_handle_mcp_notification(self, notification: str, channel_id: str, current_user: str) -> None:
        cli_notif = ClientNotification(json.loads(notification))
        current_user = self.current_user_model.model_validate_json(current_user)

        if isinstance(cli_notif.root, CancelledNotification):
            cancelled_id = cli_notif.root.params.requestId
            task_id = self._generate_response_task_id(cancelled_id, current_user, channel_id)
            task = AsyncResult(task_id)
            
            if not (task.successful() or task.failed()):
                self.worker.control.revoke(task_id)
            

        if isinstance(cli_notif.root, ProgressNotification):
            progress_id = cli_notif.root.params.progressToken
            task_id = self._generate_response_task_id(progress_id, current_user, channel_id)
            task = AsyncResult(task_id)
            if not (task.successful() or task.failed() or task.state  == states.REVOKED):
                task.backend.store_result(
                    task_id,
                    result=cli_notif.root.model_dump_json(by_alias=True, exclude_none=True),
                    state=MCP_CELERY_PROGRESS_STATE,
                )

        
        if type(cli_notif.root) in self.mcp_server.notification_handlers:
            try:
                handler = self.mcp_server.notification_handlers[type(cli_notif.root)]
                await handler(cli_notif.root)
            except Exception as err:
                pass

    def task_handle_mcp_response(self, response: str, channel_id: str, current_user: str) -> None:
        return async_to_sync(self.task_async_handle_mcp_response)(response, channel_id, current_user)
    
    async def task_async_handle_mcp_response(self, response: str, channel_id: str, current_user: str) -> str:
        return response
    
    def task_terminate_session(self, channel_id: str, current_user: str) -> None:
        current_user = self.current_user_model.model_validate_json(current_user)
        session = OdinWorkerSession(channel_id, current_user, self.mcp_server.create_initialization_options())
        session.terminate()
        pass
        
        
        