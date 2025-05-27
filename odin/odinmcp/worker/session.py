
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
from mcp.types import InitializeRequestParams
from odinmcp.models.auth import CurrentUserT



# TODO: create a custom session
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
        response: SendResultT,
        request_id: int,
    ) -> None:
        print(f"_send_response called with response={response}, request_id={request_id}")
        pass

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



    
