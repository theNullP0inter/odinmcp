
import hashlib
from typing import Any, Callable, Type
from datetime import timedelta
import uuid
from mcp.shared.exceptions import McpError
from mcp.types import (
    ClientRequest, ProgressNotification, ServerRequest, ClientNotification, ServerNotification, ClientResult, ServerResult
)
from mcp.shared.session import (
    SendRequestT, SendResultT, SendNotificationT, ReceiveResultT, ProgressFnT, RequestId
)
from mcp.shared.message import MessageMetadata, SessionMessage, ServerMessageMetadata
from mcp.server.lowlevel.server import Server as MCPServer
from celery import Celery
from odinmcp.constants import MCP_CELERY_PROGRESS_STATE
from odinmcp.config import settings
from mcp.types import JSONRPCRequest
from odinmcp.models.auth import CurrentUser
import json
from mcp.client.session import ClientSession
from asgiref.sync import async_to_sync
from contextlib import AbstractAsyncContextManager, AsyncExitStack, asynccontextmanager
from mcp.server.lowlevel.server import Server as MCPServer
from mcp.server.session import ServerSession
from mcp.server.lowlevel.server import LifespanResultT
from mcp.server.models import InitializationOptions
from mcp.types import InitializeRequestParams, JSONRPCResponse, JSONRPCError, JSONRPCMessage
from odinmcp.models.auth import CurrentUserT
from odinmcp.config import settings
import zmq
import json
from mcp.types import ErrorData, JSONRPCNotification
import requests
import time
from pydantic import BaseModel
from celery.result import AsyncResult





class OdinWorkerSession( ServerSession ):
    
    _client_params: InitializeRequestParams | None = None
    
    def __init__(
        self,
        channel_id:str,
        current_user: CurrentUserT,
        init_options: InitializationOptions,    
        response_task_id_generator: Callable[[str, CurrentUserT, str], str],
    ) -> None:
        self._init_options = init_options
        self._current_user = current_user   
        self._channel_id = channel_id
        self._response_task_id_generator = response_task_id_generator

        client_params =self._current_user.get_client_params(self._channel_id)
        self._client_params = client_params        
                

    def get_hermod_socket(self) -> zmq.Socket:
        zmq_context = zmq.Context()
        hermod_socket = zmq_context.socket(zmq.PUB)
        for url in settings.hermod_zero_mq_urls:
            hermod_socket.connect(url)
        return hermod_socket

    def terminate(self):
        hermod_socket = self.get_hermod_socket()
        item = {
            "channel": self._channel_id,
            "formats":{
                "http-stream": {
                    "action":"close",
                }
            }
        }
        # TODO: wait till socket is ready instead of time
        time.sleep(0.1)
        hermod_socket.send_multipart(
            [
                self._channel_id.encode(),
                ("J" + json.dumps(item)).encode(),
            ]
        )
        
        
    
    def send_sse_message(self, message: SessionMessage) -> None:
        hermod_socket = self.get_hermod_socket()
        
        content = "event: message\ndata: " + message.message.model_dump_json(by_alias=True, exclude_none=True)
        item = {
            "channel": self._channel_id,
            "formats":{
                "http-stream": {
                    "content": content +"\n\n"
                }
            }
        }
        # TODO: wait till socket is ready instead of time
        time.sleep(0.1)
        hermod_socket.send_multipart(
            [
                self._channel_id.encode(),
                ("J" + json.dumps(item)).encode(),
            ]
        )
        
    
    async def send_request(
        self,
        request: SendRequestT,
        result_type: type[ReceiveResultT],
        request_read_timeout_seconds: timedelta = timedelta(seconds=3),
        metadata: MessageMetadata = None,
        progress_callback: ProgressFnT | None = None,
    ) -> ReceiveResultT:
        
        request_id = str(uuid.uuid4())
        request_data = request.model_dump(by_alias=True, mode="json", exclude_none=True)

        response_task_id = self._response_task_id_generator(request_id, self._current_user, self._channel_id)

        # Set up progress token if progress callback is provided
        if progress_callback is not None:
            if "params" not in request_data:
                request_data["params"] = {}
            if "_meta" not in request_data["params"]:
                request_data["params"]["_meta"] = {}
            request_data["params"]["_meta"]["progressToken"] = request_id
            
        jsonrpc_request = JSONRPCRequest(
            jsonrpc="2.0",
            id=request_id,
            **request_data,
        )
        session_message = SessionMessage(
            message=JSONRPCMessage(jsonrpc_request),
            metadata=metadata,
        )
        self.send_sse_message(session_message)

        
        start_time = time.time()
        current_progress = None
        while True:
            result  = AsyncResult(response_task_id)
            if progress_callback is not None:
                if result.state == MCP_CELERY_PROGRESS_STATE:
                    if current_progress != result.result["progress"]:
                        current_progress = result.result["progress"]
                        progress_notif = ProgressNotification.model_validate_json(current_progress)
                        progress_callback(
                            progress=progress_notif.params.progress,
                            total=progress_notif.params.total,
                            message=progress_notif.params.message,
                        )

            if result.successful() or result.failed():
                break            
            if time.time() - start_time > request_read_timeout_seconds.total_seconds():
                raise McpError("Request timeout")
            time.sleep(0.1)

        response: str =  result.result
        jsonrpc_response = JSONRPCMessage(root=json.loads(response))
        if isinstance(jsonrpc_response.root, JSONRPCError):
            raise McpError(jsonrpc_response.root.error)
        elif isinstance(jsonrpc_response.root, JSONRPCResponse):
            return result_type.model_validate(jsonrpc_response.root.result)
        else:
            raise McpError("Invalid response")
        
        

        


    async def send_notification(
        self,
        notification: SendNotificationT,
        related_request_id: RequestId | None = None,
    ) -> None:
        jsonrpc_notification = JSONRPCNotification(
            jsonrpc="2.0",
            **notification.model_dump(by_alias=True, mode="json", exclude_none=True),
        )
        session_message = SessionMessage(
            message=JSONRPCMessage(jsonrpc_notification),
            metadata=ServerMessageMetadata(related_request_id=related_request_id)
            if related_request_id
            else None,
        )
        self.send_sse_message(session_message)

    async def _send_response(
        self,
        response: SendResultT | ErrorData,
        request_id: RequestId,
    ) -> None:
        if isinstance(response, ErrorData):
            jsonrpc_error = JSONRPCError(jsonrpc="2.0", id=request_id, error=response)
            message = JSONRPCMessage(jsonrpc_error)
        else:
            jsonrpc_response = JSONRPCResponse(
                jsonrpc="2.0",
                id=request_id,
                result=response.model_dump(
                    by_alias=True, mode="json", exclude_none=True
                ),
            )
            message = JSONRPCMessage(jsonrpc_response)
        session_message = SessionMessage(message=message)
        self.send_sse_message(session_message)

    
    # Below methods are used with server.run() . Since we are not using server.run() we are not implementing them
    async def _receive_loop(self) -> None:
        raise NotImplementedError

    async def _handle_incoming(self, message: Any) -> None:
        raise NotImplementedError
    
    async def _received_request(
        self, responder: Any
    ) -> None:
        raise NotImplementedError
    
    async def run(self) -> None:
        raise NotImplementedError



    
