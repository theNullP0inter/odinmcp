from odinmcp.web.transports.http_streaming import OdinHttpStreamingTransport
from odinmcp.web.middleware.heimdall import HeimdallCurrentUserMiddleware
from odinmcp.web.middleware.hermod import HermodStreamingMiddleware
from odinmcp.config import settings
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware import Middleware
from odinmcp.models.auth import CurrentUser
from mcp.server.lowlevel.server import Server as MCPServer
from typing import Type, List

class OdinWeb:

    def __init__(
        self,
        mcp_server: MCPServer,
        current_user_model: Type[CurrentUser] = CurrentUser,
        extra_middleware:List[Middleware] = [] 
    ):
        self.mcp_server = mcp_server
        self.current_user_model = current_user_model
        self.extra_middleware = extra_middleware
        

    
    def build(self):


        async def handle_mcp_request(
            request: Request,
        ) -> Response:
            transport = OdinHttpStreamingTransport(self.mcp_server, request)
            return await transport.get_response()
        

        # TODO: create a new messages endpoint to support legacy SSE

        mcp_app = Starlette(
            debug=settings.debug,
            middleware=[
                Middleware(BaseHTTPMiddleware, dispatch=HeimdallCurrentUserMiddleware(self.current_user_model)),
                Middleware(BaseHTTPMiddleware, dispatch=HermodStreamingMiddleware())
            ] + self.extra_middleware,
            routes=[
                Route( 
                    "/", 
                    endpoint=handle_mcp_request, 
                    methods=["GET", "POST", "DELETE"],
                ),
            ],
        )
        
        return mcp_app
        