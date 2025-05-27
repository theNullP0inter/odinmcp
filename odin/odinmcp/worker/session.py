
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
from mcp.server.lowlevel.server import LifespanResultT
from mcp.server.models import InitializationOptions
from mcp.types import InitializeRequestParams, JSONRPCResponse, JSONRPCError, JSONRPCMessage
from odinmcp.models.auth import CurrentUserT
from odinmcp.config import settings
import zmq
import json
from mcp.types import ErrorData
import requests
import time



# hermod_socket.connect("tcp://hermod:5562")
# time.sleep(0.1)

# for url in settings.hermod_zero_mq_urls:
#     print(f"Connecting to hermod zero mq url: {url}")
#     hermod_socket.connect(url)
    


class OdinWorkerSession( ServerSession ):
    
    _client_params: InitializeRequestParams | None = None
    
    def __init__(
        self,
        channel_id:str,
        current_user: CurrentUserT,
        init_options: InitializationOptions,    
    ) -> None:
        self._init_options = init_options
        self._current_user = current_user   
        self._channel_id = channel_id

        client_params =self._current_user.get_client_params(self._channel_id)
        self._client_params = client_params        
                

    def get_hermod_socket(self) -> zmq.Socket:
        zmq_context = zmq.Context()
        hermod_socket = zmq_context.socket(zmq.PUB)
        for url in settings.hermod_zero_mq_urls:
            hermod_socket.connect(url)
        return hermod_socket
        
    

    async def send_request(
        self,
        request: SendRequestT,
        result_type: type[ReceiveResultT],
        request_read_timeout_seconds: timedelta | None = None,
        metadata: MessageMetadata = None,
        progress_callback: ProgressFnT | None = None,
    ) -> ReceiveResultT:
        print(f"send_request called with request={request}, result_type={result_type}, request_read_timeout_seconds={request_read_timeout_seconds}, metadata={metadata}, progress_callback={progress_callback}")
        pass


    async def send_notification(
        self,
        notification: SendNotificationT,
        metadata: MessageMetadata = None,
    ) -> None:
        print(f"send_notification called with notification={notification}, metadata={metadata}")
        pass

    async def _send_response(
        self,
        response: SendResultT | ErrorData,
        request_id: int,
    ) -> None:
        print(f"_send_response called with response={response}, request_id={request_id}")
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
        
        
        content = "event: message\ndata: " + message.model_dump_json(by_alias=True, exclude_none=True)
        
        item = {
            "channel": self._channel_id,
            "formats":{
                "http-stream": {
                    "content": content +"\n\n"
                }
            }
        }

        
        hermod_socket = self.get_hermod_socket()
        # TODO: wait till socket is ready instead of time
        time.sleep(0.1)


        hermod_socket.send_multipart(
            [
                self._channel_id.encode(),
                ("J" + json.dumps(item)).encode(),
                # "\n\n".encode(),
            ]
        )

        
    
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



    
