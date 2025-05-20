import json
from uuid import uuid4
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.exceptions import HTTPException
from starlette.types import Receive, Scope, Send
from mcp.types import JSONRPCMessage, JSONRPCResponse
from monitors.logging import logger
from models.user import User
from core.config import settings
from odinmcp.server.sse import OdinSseServerTransport

class OdinMCP(FastMCP):
    organization_path_param = "org_code"
    mcp_route_prefix = "mcp"
    
    def sse_app(self):
        sse = OdinSseServerTransport(self.settings.message_path)
        
        def check_user_access(request: Request, org_code: str)->User:
            user: User = request.state.user
            if not user:
                raise HTTPException(status_code=401, detail='Unauthorized')
            
            if org_code not in user.organizations:
                raise HTTPException(status_code=403, detail='Forbidden. User does not have access to this organization')
            return user

        async def handle_sse(request: Request) -> None:
            # check_user_access(request, request.path_params[self.organization_path_param])
            
            
            
            channel_id = request.headers.get("mcp-session-id") or str(uuid4())
            # session_uri = settings.ROOT_PATH +f"/{self.mcp_route_prefix}/"+ request.path_params[self.organization_path_param]+"/"+ self.settings.message_path +f"?session_id={channel_id}"
            # logger.debug(f"Session URI: {session_uri}")
            if not request.state.supports_hermod_streaming:
                pass
            # TODO: add content like in server.run
            # data = {"event": "endpoint", "data": session_uri}
            if request.method == "GET":
                print("GET request")
                return Response(
                    # status_code=405,
                    # headers={
                    #     "Grip-Hold": "stream",
                    #     "Content-Type": "text/event-stream",
                    #     "Grip-Channel": f"{channel_id}",
                    #     "mcp-session-id": channel_id,
                    # }
                )
                # send messages endpoint also -> sometimes -> when exactly?
                
            if request.method == "POST":
                # 1. Initialize request
                # if initializeRequest  send initializeResponse with a new session_id
                #     is_initialization_request = (
                #     isinstance(message.root, JSONRPCRequest)
                #     and message.root.method == "initialize"
                # )
                
                
                
                
                # jsonrpc_response = JSONRPCResponse(
                #     jsonrpc="2.0",
                #     id=request_id,
                #     result=response.model_dump(
                #         by_alias=True, mode="json", exclude_none=True
                #     ),
                # )
                
                initialize_response = {
                    "jsonrpc": "2.0",
                    "id": 0,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                        "logging": {},
                        "prompts": {
                            "listChanged": True
                        },
                        "resources": {
                            "subscribe": True,
                            "listChanged": True
                        },
                        "tools": {
                            "listChanged": True
                        }
                        },
                        "serverInfo": {
                        "name": "ExampleServer",
                        "version": "1.0.0"
                        }
                    }
                }
                req = await request.body()
                print(req)
                
                res = JSONRPCResponse(
                    jsonrpc="2.0",
                    id=0,
                    result=initialize_response.get("result"),
                )
                # if http-streaming
                return Response(
                    status_code=200,
                    content=res.model_dump_json(),
                    headers={
                        # "Grip-Hold": "stream",
                        # "Grip-Channel": channel_id,
                        "Content-Type": "application/json",
                        # "Accept": "application/json",
                        # "Content-Type": "text/event-stream",
                        # "MCP-Session-Id": channel_id,
                        "mcp-session-id": channel_id,
                    }
                )
                
                # if sse -> content-type: text/event-stream
                
                
                # 2. Initialized notification
                # if initializedNotification with session_id -> send 202 accepted
            
            # if request.method == "DELETE":
            #  terminate the session
        
        
        async def handle_post_message(scope: Scope, receive: Receive, send: Send) -> None:
            request = Request(scope, receive)
            check_user_access(request, request.path_params[self.organization_path_param])
            logger.debug(f"Handling POST message for organization {request.path_params[self.organization_path_param]}")
            return await sse.handle_post_message(scope, receive, send)
            
        return Starlette(
            debug=self.settings.debug,
            routes=[
                Route(self.settings.sse_path, endpoint=handle_sse, methods=["GET", "POST"]),
            ],
        )