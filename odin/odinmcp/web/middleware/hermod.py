import logging
from starlette.exceptions import HTTPException
from starlette.requests import Request
from odinmcp.models.auth import CurrentUser
from odinmcp.config import settings
from mcp.types import (
    JSONRPCMessage, JSONRPCResponse, InitializeResult, JSONRPCRequest,
    JSONRPCError, ErrorData, PARSE_ERROR, INVALID_REQUEST, INVALID_PARAMS,
    INTERNAL_ERROR, LATEST_PROTOCOL_VERSION, LoggingCapability,
    PromptsCapability, ResourcesCapability, ToolsCapability,
)
from odinmcp.constants import (
    MCP_SESSION_ID_HEADER,
    LAST_EVENT_ID_HEADER,
    CONTENT_TYPE_HEADER,
    ACCEPT_HEADER,
    CONTENT_TYPE_JSON,
    CONTENT_TYPE_SSE,
)
from http import HTTPStatus



class HermodStreamingMiddleware:
    async def __call__(self, request: Request, call_next):
        # existing hermod bypass
        supports_hermod_streaming = (request.headers.get(settings.hermod_streaming_header, "false") == "true")
        
        accept_hdr = request.headers.get(ACCEPT_HEADER, "")
        
        if not supports_hermod_streaming and CONTENT_TYPE_SSE in accept_hdr:
            request.headers[ACCEPT_HEADER] = accept_hdr.replace(CONTENT_TYPE_SSE, "")
            supports_hermod_streaming = False
        elif supports_hermod_streaming and CONTENT_TYPE_JSON in accept_hdr:
            supports_hermod_streaming = True
            
        setattr(request.state, settings.supports_hermod_streaming_state, supports_hermod_streaming)
        
        # 1. if mcp-session-id exists -> it should be valid   
        channel_id = request.headers.get(MCP_SESSION_ID_HEADER, None)
        user  = getattr(request.state, settings.current_user_state, None)
        
        if channel_id and not (user and user.validate_hermod_streaming_token(channel_id)):
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail="User not found",
                headers={MCP_SESSION_ID_HEADER: channel_id}
            )
        
        
        # 2. Not Acceptable
        if CONTENT_TYPE_JSON not in accept_hdr and CONTENT_TYPE_SSE not in accept_hdr:
            raise HTTPException(
                status_code=HTTPStatus.NOT_ACCEPTABLE,
                detail=f"Client must accept {CONTENT_TYPE_JSON} or {CONTENT_TYPE_SSE}",
                headers={MCP_SESSION_ID_HEADER: channel_id} if channel_id else {}
            )
        
        # TODO: 3. Unsupported Content-Type
        
        
        return await call_next(request)
