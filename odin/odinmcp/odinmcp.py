from http import HTTPStatus
import json
from typing import Any, Generic, Optional
from mcp.server.lowlevel.server import LifespanResultT
from uuid import uuid4
from mcp.server.fastmcp import FastMCP 
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.exceptions import HTTPException
from starlette.types import Receive, Scope, Send
from mcp.types import JSONRPCMessage, JSONRPCResponse, InitializeResult, JSONRPCRequest, JSONRPCError, ErrorData, PARSE_ERROR, INVALID_REQUEST, INVALID_PARAMS, INTERNAL_ERROR, LATEST_PROTOCOL_VERSION, LoggingCapability, PromptsCapability, ResourcesCapability, ToolsCapability
from monitors.logging import logger
# from core.config import settings # Assuming settings might be used elsewhere or was a previous import
from mcp.server.lowlevel.server import Server as MCPServer, NotificationOptions
# from mcp.types import InitializeResult, JSONRPCRequest, JSONRPCResponse # Duplicate, covered above
from contextlib import AbstractAsyncContextManager, AsyncExitStack, asynccontextmanager
from collections.abc import AsyncIterator, Awaitable, Callable, Iterable
from pydantic_settings import BaseSettings, SettingsConfigDict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware import Middleware

from odinmcp.middleware.heimdall import CurrentUserMiddleware
from odinmcp.middleware.hermod import HermodStreamingMiddleware
from odinmcp.config import settings
from odinmcp.constants import (
    MCP_SESSION_ID_HEADER,
    LAST_EVENT_ID_HEADER,
    CONTENT_TYPE_HEADER,
    ACCEPT_HEADER,
    CONTENT_TYPE_JSON,
    CONTENT_TYPE_SSE,
)



MIDDLEWARE = [
    Middleware(BaseHTTPMiddleware, dispatch=CurrentUserMiddleware()),
    Middleware(BaseHTTPMiddleware, dispatch=HermodStreamingMiddleware())
]





class OdinMCP:
    
    
    def __init__(
        self,
        name: str,
        instructions: str,
        version: str | None = None,
    ):  
        self._mcp_server = MCPServer(
            name=name,
            instructions=instructions,
            version=version or "0.1.0",
        )
        
        # Note: this is a placeholder for the actual settings to make it work with the mcp-inspector
        #  store self._mcp_server.create_initialization_options() for cache
        mcp_initialization_options = self._mcp_server.create_initialization_options(
            notification_options=NotificationOptions(),
            experimental_capabilities={},
        )
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
        
        self.mcp_initialize_result = InitializeResult(
                protocolVersion=LATEST_PROTOCOL_VERSION,
                capabilities=mcp_initialization_options.capabilities,
                serverInfo={ 
                    "name": mcp_initialization_options.server_name,
                    "version": mcp_initialization_options.server_version,
                },
                instructions=self._mcp_server.instructions,
                meta={},
        )
    
    
    def _create_error_response(
        self,
        error_message: str,
        status_code: HTTPStatus,
        error_code: int = INVALID_REQUEST,
        headers: dict[str, str] | None = None,
    ) -> Response:
        """Create a JSON-RPC error response."""
        response_headers = {CONTENT_TYPE_HEADER: CONTENT_TYPE_JSON}
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
        response_headers = {CONTENT_TYPE_HEADER: CONTENT_TYPE_JSON}
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
        
    # TODO: _create_streaming_response
    
    
    def app(self ) -> Starlette:
        
        
        async def handle_request(request: Request) -> Response:
            org = request.path_params[settings.organization_path_param]
            channel_id = request.headers.get(MCP_SESSION_ID_HEADER) or str(uuid4())

            meth = request.method.upper()
            if meth == "GET":
                return await self._handle_get(request, channel_id)
            elif meth == "POST":
                return await self._handle_post(request, channel_id)
            elif meth == "DELETE":
                return await self._handle_delete(request, channel_id)
            else:
                # For Method Not Allowed, a simple HTTP response is fine,
                # but if you want JSON-RPC, you could use _create_error_response
                raise HTTPException(status_code=HTTPStatus.METHOD_NOT_ALLOWED, detail="Method not allowed")

        
        mcp_app = Starlette(
            debug=settings.debug,
            routes=[
                Route( 
                "/{"+settings.organization_path_param +"}", 
                endpoint=handle_request, 
                methods=["GET", "POST", "DELETE"],
                middleware=MIDDLEWARE,
                ),
            ],
        )
        
        
        return mcp_app
        

    async def _handle_get(self, request: Request, channel_id: str) -> Response:
        # TODO: handle GET request. start streaming.
        logger.info(f"GET request received for channel_id: {channel_id}. Not yet implemented.")
        return self._create_error_response(
            error_message="Method Not Allowed. This endpoint is for MCP POST requests or future GET streaming.",
            status_code=HTTPStatus.METHOD_NOT_ALLOWED,
            headers={MCP_SESSION_ID_HEADER: channel_id},
            error_code=INTERNAL_ERROR # Or a more specific code if available
        )

    async def _handle_post(self, request: Request, channel_id: str) -> Response:
        
        # 1: try to parse the request body as JSON. except and handle
        try:
            body = await request.body()
            if not body:
                logger.warning(f"Client sent an empty POST request body for session {channel_id}.")
                return self._create_error_response(
                    error_message="Request body cannot be empty for POST.",
                    status_code=HTTPStatus.BAD_REQUEST, # 400
                    headers={MCP_SESSION_ID_HEADER: channel_id},
                    error_code=INVALID_REQUEST
                )
            json_data = json.loads(body)

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON body for session {channel_id}: {e}")
            return self._create_error_response(
                error_message="Parse error: Invalid JSON was received by the server.",
                status_code=HTTPStatus.BAD_REQUEST, # 400
                headers={MCP_SESSION_ID_HEADER: channel_id},
                error_code=PARSE_ERROR
            )

        # 2. should be JSONRPCMessage
        try:
            message = JSONRPCMessage.model_validate(json_data)
            
        except Exception as e:  
            logger.warning(f"Failed to validate JSONRPCMessage for session {channel_id}: {e}. Data: {json_data}")
            return self._create_error_response(
                error_message="Invalid Request: The JSON sent is not a valid Request object.",
                status_code=HTTPStatus.BAD_REQUEST, # 400
                headers={MCP_SESSION_ID_HEADER: channel_id},
                error_code=INVALID_REQUEST # Or INVALID_PARAMS if structure is okay but content is bad
            )

        # 3. check if initialize request
        if isinstance(message.root, JSONRPCRequest) and message.root.method == "initialize":
            req_id = message.root.id
            
        
            response_message = JSONRPCResponse(
                id=req_id,
                result=self.mcp_initialize_result.model_dump(),
                jsonrpc=message.root.jsonrpc or "2.0" 
            )
            
            res =  self._create_json_response(
                response_message,
                status_code=HTTPStatus.OK,
                headers={MCP_SESSION_ID_HEADER: channel_id},
            )
            logger.info(f"Successful 'initialize' request for session {channel_id}.")
            logger.info(
                f"Response: {response_message.model_dump_json(exclude_none=True)}"
            )
            return res
            
        else:
            # Handle other JSONRPC messages (non-initialize POST)
            logger.info(f"Received non-initialize JSONRPC message on session {channel_id}: {message.model_dump_json(exclude_none=True)}")
            
            # TODO: handle notifications initialize -> send grip headers
            
            
            
            

    async def _handle_delete(self, request: Request, channel_id: str) -> Response:
        # TODO: handle DELETE request. terminate session.
        logger.info(f"DELETE request received for session {channel_id}. Terminating session.")
        return Response(status_code=HTTPStatus.NO_CONTENT, headers={MCP_SESSION_ID_HEADER: channel_id})

