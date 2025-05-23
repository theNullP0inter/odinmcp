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

# from core.config import settings # Assuming settings might be used elsewhere or was a previous import
from mcp.server.lowlevel.server import Server as MCPServer, NotificationOptions
# from mcp.types import InitializeResult, JSONRPCRequest, JSONRPCResponse # Duplicate, covered above
from contextlib import AbstractAsyncContextManager, AsyncExitStack, asynccontextmanager
from collections.abc import AsyncIterator, Awaitable, Callable, Iterable
from pydantic_settings import BaseSettings, SettingsConfigDict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware import Middleware

from odinmcp.models.auth import CurrentUser
from odinmcp.web.middleware.heimdall import HeimdallCurrentUserMiddleware
from odinmcp.web.middleware.hermod import HermodStreamingMiddleware
from odinmcp.config import settings
from odinmcp.web.transports.http_streaming import OdinHttpStreamingTransport
from odinmcp.web import OdinWeb
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

from odinmcp.config import settings
from celery import Celery
from celery.contrib.abortable import AbortableTask
from odinmcp.worker import OdinWorker




class OdinMCP:
    
    
    def __init__(
        self,
        name: str,
        instructions: Optional[str] = None,
        version: Optional[str] = None,
        current_user_model: Type[CurrentUser] = CurrentUser,
        
    ):  
        self.mcp_server = MCPServer(
            name=name,
            instructions=instructions,
            version=version,
        )
        self.worker = OdinWorker(
            self.mcp_server,
            current_user_model,
        )
        self.web = OdinWeb(
            self.mcp_server,
            current_user_model,
            self.worker,
        )

        self.current_user_model = current_user_model
        
        
        
    def sse_app(
        self,  
        extra_middleware:List[Middleware] = []
    ) -> Starlette:
        return self.web.build(extra_middleware=extra_middleware), self.worker.get_worker()
        

        

