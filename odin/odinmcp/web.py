from http import HTTPStatus
import json
from typing import Any, Generic, List, Optional, Type
from mcp.server.lowlevel.server import LifespanResultT
from uuid import uuid4
from mcp.server.fastmcp import FastMCP 
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.exceptions import HTTPException
from starlette.types import Receive, Scope, Send
from mcp.types import JSONRPCMessage, JSONRPCResponse, InitializeResult, JSONRPCRequest, JSONRPCError, ErrorData, PARSE_ERROR, INVALID_REQUEST, INVALID_PARAMS, INTERNAL_ERROR, LATEST_PROTOCOL_VERSION, LoggingCapability, PromptsCapability, ResourcesCapability, ToolsCapability, JSONRPCNotification
from monitors.logging import logger
# from core.config import settings # Assuming settings might be used elsewhere or was a previous import
from mcp.server.lowlevel.server import Server as MCPServer, NotificationOptions
# from mcp.types import InitializeResult, JSONRPCRequest, JSONRPCResponse # Duplicate, covered above
from contextlib import AbstractAsyncContextManager, AsyncExitStack, asynccontextmanager
from collections.abc import AsyncIterator, Awaitable, Callable, Iterable
from pydantic_settings import BaseSettings, SettingsConfigDict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware import Middleware

from odinmcp.models.auth import CurrentUser
from odinmcp.middleware.heimdall import HeimdallCurrentUserMiddleware
from odinmcp.middleware.hermod import HermodStreamingMiddleware
from odinmcp.config import settings
from odinmcp.constants import (
    MCP_SESSION_ID_HEADER,
    LAST_EVENT_ID_HEADER,
    CONTENT_TYPE_HEADER,
    ACCEPT_HEADER,
    CONTENT_TYPE_JSON,
    CONTENT_TYPE_SSE,
    HERMOD_GRIP_HOLD_HEADER,
    HERMOD_GRIP_HOLD_MODE,
    HERMOD_GRIP_CHANNEL_HEADER
)


class OdinWeb:
    def __init__(
        self,
        mcp_server: MCPServer,
        request: Request  
    ):
        
        self.mcp_server = mcp_server
        self.request = request
        self.supports_hermod_streaming = getattr(request.state, settings.supports_hermod_streaming_state, False)
        self.current_user = getattr(request.state, settings.current_user_state, None)
        self.channel_id = self.request.headers.get(MCP_SESSION_ID_HEADER) or self.create_new_user_channel()
    
    
    def get_initialize_result(self) -> InitializeResult:
        mcp_initialization_options = self.mcp_server.create_initialization_options(
            notification_options=NotificationOptions(),
            experimental_capabilities={},
        )
        
        # TODO: Remove the capability manipulation once server is fully implemented
        #  Note: this is a placeholder for the actual settings to make it work with the mcp-inspector
        
        mcp_initialization_options.capabilities.logging = LoggingCapability()
        mcp_initialization_options.capabilities.prompts = PromptsCapability(
            listChanged=True,
        )
        mcp_initialization_options.capabilities.resources = ResourcesCapability(
            subscribe=True,
            listChanged=True,
        )
        mcp_initialization_options.capabilities.tools = ToolsCapability(
            listChanged=True,
        )
        
        return InitializeResult(
                protocolVersion=LATEST_PROTOCOL_VERSION,
                capabilities=mcp_initialization_options.capabilities,
                serverInfo={ 
                    "name": mcp_initialization_options.server_name,
                    "version": mcp_initialization_options.server_version,
                },
                instructions=self.mcp_server.instructions,
                meta={},
        )
            
        
    async def get_response(self) -> Response:
        
        method = self.request.method.upper()
        if method == "GET":
            return await self._handle_get() # -> Needs a validated session
        elif method == "POST":
            return await self._handle_post() # -> Needs a validated session. Doesnt need for initialize
        elif method == "DELETE":
            return await self._handle_delete() # -> Needs a validated session
        else:
            # For Method Not Allowed, a simple HTTP response is fine,
            # but if you want JSON-RPC, you could use _create_error_response
            raise HTTPException(status_code=HTTPStatus.METHOD_NOT_ALLOWED, detail="Method not allowed")
    
    
    async def _handle_get(self ) -> Response:
        
        if not self.supports_hermod_streaming:
            
            return self._create_error_response(
                error_message="Client must accept application/json or text/event-stream",
                status_code=HTTPStatus.NOT_ACCEPTABLE, # 406
                error_code=INVALID_REQUEST
            )
        if self.channel_id: 
            return self._create_streaming_hold_response(self.channel_id)
        else:
            # TODO: support legacy sse by returning endpoint event
            return self._create_error_response(
                error_message="Session ID is required for GET.",
                status_code=HTTPStatus.BAD_REQUEST, # 400
                error_code=INVALID_REQUEST
            )
    
    async def _handle_delete(self) -> Response:
        # TODO: handle DELETE request. terminate session.
        if not self.channel_id:
            return self._create_error_response(
                error_message="Session ID is required for DELETE.",
                status_code=HTTPStatus.BAD_REQUEST, # 400
                error_code=INVALID_REQUEST
            )
        return self._create_json_response(
            response_message=None,
            status_code=HTTPStatus.OK
        )
        
        

    async def _handle_post(self) -> Response:
        
        # 1: try to parse the request body as JSON. except and handle
        try:
            body = await self.request.body()
            if not body:

                return self._create_error_response(
                    error_message="Request body cannot be empty for POST.",
                    status_code=HTTPStatus.BAD_REQUEST, # 400
                    error_code=INVALID_REQUEST
                )
            json_data = json.loads(body)

        except json.JSONDecodeError as e:
            
            return self._create_error_response(
                error_message="Parse error: Invalid JSON was received by the server.",
                status_code=HTTPStatus.BAD_REQUEST, # 400
                error_code=PARSE_ERROR
            )

        # 2. should be JSONRPCMessage
        try:
            message = JSONRPCMessage.model_validate(json_data)
            
        except Exception as e:  
            return self._create_error_response(
                error_message="Invalid Request: The JSON sent is not a valid Request object.",
                status_code=HTTPStatus.BAD_REQUEST, # 400
                error_code=INVALID_REQUEST # Or INVALID_PARAMS if structure is okay but content is bad
            )

        # 3. check if initialize request
        if isinstance(message.root, JSONRPCRequest) and message.root.method == "initialize":
            req_id = message.root.id
            
            response_message = JSONRPCResponse(
                id=req_id,
                result=self.get_initialize_result().model_dump(by_alias=True, exclude_none=True),
                jsonrpc=message.root.jsonrpc or "2.0" 
            )
            
            self.channel_id = self.create_new_user_channel()
            return self._create_json_response(
                response_message,
                status_code=HTTPStatus.OK,
            )
        
        if not self.channel_id:
            return self._create_error_response(
                error_message="Session ID is required for POST.",
                status_code=HTTPStatus.BAD_REQUEST, # 400
                error_code=INVALID_REQUEST
            )
        
            
        if isinstance(message.root, JSONRPCRequest):
            # TODO: trigger tasks -> requests that are not initialize
            pass
        elif isinstance(message.root, JSONRPCNotification):
            
            if message.root.method == "notifications/initialized" and self.supports_hermod_streaming:
                res = self._create_streaming_hold_response(
                    self.channel_id,
                )
            else:
                #  send 202 json response
                res = self._create_json_response(
                    response_message=None,
                    status_code=HTTPStatus.ACCEPTED,
                )

            # TODO: trigger tasks for non-initialize notifications
            return res            
        else:
            return self._create_error_response(
                error_message="Invalid Request: The JSON sent is not a valid Request object.",
                status_code=HTTPStatus.BAD_REQUEST, # 400
                error_code=INVALID_REQUEST # Or INVALID_PARAMS if structure is okay but content is bad
            )
            
            
    

    
    def _create_error_response(
        self,
        error_message: str,
        status_code: HTTPStatus,
        error_code: int = INVALID_REQUEST,
        headers: dict[str, str] | None = None,
    ) -> Response:
        """Create a JSON-RPC error response."""
        response_headers = {
            CONTENT_TYPE_HEADER: CONTENT_TYPE_JSON,
            MCP_SESSION_ID_HEADER: self.channel_id,
        }
        if headers:
            response_headers.update(headers)

        error_data = ErrorData(code=error_code, message=error_message)
        json_rpc_error = JSONRPCError(
            jsonrpc="2.0",
            id=None,  # JSON-RPC errors can have a null id
            error=error_data,
        )

        return Response(
            json_rpc_error.model_dump_json(by_alias=True, exclude_none=True),
            status_code=status_code,
            headers=response_headers,
        )
    
    def _create_json_response(
        self,
        response_message: JSONRPCMessage | None,
        status_code: HTTPStatus = HTTPStatus.OK,
        headers: dict[str, str] | None = None,
    ) -> Response:
        """Create a JSON response from a JSONRPCMessage"""
        response_headers = {
            CONTENT_TYPE_HEADER: CONTENT_TYPE_JSON,
            MCP_SESSION_ID_HEADER: self.channel_id,
        }
        if headers:
            response_headers.update(headers)
        logger.info(f"Creating JSON response with headers: {response_headers}")
        return Response(
            response_message.model_dump_json(by_alias=True, exclude_none=True)
            if response_message
            else None,
            status_code=status_code,
            headers=response_headers,
        )
        
    def _create_streaming_hold_response(
        self,
        channel_id,
        status_code: HTTPStatus = HTTPStatus.ACCEPTED,
        headers: dict[str, str] | None = None,
    ) -> Response:
        """Create a streaming hold response"""
        response_headers = {
            CONTENT_TYPE_HEADER: CONTENT_TYPE_SSE, 
            HERMOD_GRIP_HOLD_HEADER: HERMOD_GRIP_HOLD_MODE,
            HERMOD_GRIP_CHANNEL_HEADER: channel_id,
            MCP_SESSION_ID_HEADER: channel_id,
            ACCEPT_HEADER: CONTENT_TYPE_JSON,
        }
        # TODO: generate channel id
        # TODO: keep-alive headers
        if headers:
            response_headers.update(headers)

        return Response(
            content=None,
            status_code=status_code,
            headers=response_headers,
        )

    def create_new_user_channel(self) -> str:
        """Create a new user channel"""
        user : CurrentUser = getattr(self.request.state, settings.current_user_state, None)
        return user.create_hermod_streaming_token()