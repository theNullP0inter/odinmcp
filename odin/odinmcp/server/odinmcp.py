from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Mount, Route
from starlette.exceptions import HTTPException
from starlette.types import Receive, Scope, Send
from monitors.logging import logger
from models.user import User
from core.config import settings
from odinmcp.server.sse import OdinSseServerTransport

class OdinMCP(FastMCP):
    organization_path_param = "org_code"
    mcp_route_prefix = "odinmcp"
    
    def sse_app(self):
        sse = OdinSseServerTransport(self.settings.message_path)
        
        def check_user_access(request: Request, org_code: str)->User:
            user: User = request.state.user
            if not user:
                raise HTTPException(status_code=401, detail='Unauthorized')
            
            if org_code not in user.organization:
                raise HTTPException(status_code=403, detail='Forbidden. User does not have access to this organization')
            return user

        async def handle_sse(request: Request) -> None:
            check_user_access(request, request.path_params[self.organization_path_param])
            async with sse.connect_sse(
                request.scope,
                request.receive,
                request._send,  # type: ignore[reportPrivateUsage]
                settings.ROOT_PATH +f"/{self.mcp_route_prefix}/"+ request.path_params[self.organization_path_param],
            ) as streams:
                await self._mcp_server.run(
                    streams[0],
                    streams[1],
                    self._mcp_server.create_initialization_options(),
                )
        
        async def handle_post_message(scope: Scope, receive: Receive, send: Send) -> None:
            request = Request(scope, receive)
            check_user_access(request, request.path_params[self.organization_path_param])
            logger.debug(f"Handling POST message for organization {request.path_params[self.organization_path_param]}")
            return await sse.handle_post_message(scope, receive, send)
            
        return Starlette(
            debug=self.settings.debug,
            routes=[
                Route(self.settings.sse_path, endpoint=handle_sse),
                Mount(self.settings.message_path, app=handle_post_message),
            ],
        )