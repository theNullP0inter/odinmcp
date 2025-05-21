import logging
from starlette.exceptions import HTTPException
from odinmcp.server.config import settings
from mcp.types import (
    JSONRPCMessage, JSONRPCResponse, InitializeResult, JSONRPCRequest,
    JSONRPCError, ErrorData, PARSE_ERROR, INVALID_REQUEST, INVALID_PARAMS,
    INTERNAL_ERROR, LATEST_PROTOCOL_VERSION, LoggingCapability,
    PromptsCapability, ResourcesCapability, ToolsCapability,
)
from odinmcp.server.constants import (
    MCP_SESSION_ID_HEADER,
    LAST_EVENT_ID_HEADER,
    CONTENT_TYPE_HEADER,
    ACCEPT_HEADER,
    CONTENT_TYPE_JSON,
    CONTENT_TYPE_SSE,
)
from http import HTTPStatus



logger = logging.getLogger(__name__)

class HermodStreamingMiddleware:
    async def __call__(self, request, call_next):
        # existing hermod bypass
        hermod_header = request.headers.get(settings.hermod_streaming_header, "false")
        if hermod_header != "true" and CONTENT_TYPE_SSE in request.headers.get(ACCEPT_HEADER, ""):
            request.headers[ACCEPT_HEADER] = request.headers[ACCEPT_HEADER].replace(CONTENT_TYPE_SSE, "")

        # new checks:
        channel_id = request.headers.get(MCP_SESSION_ID_HEADER)
        accept_hdr = request.headers.get(ACCEPT_HEADER, "")
        # 1. Not Acceptable
        if not (CONTENT_TYPE_JSON in accept_hdr and CONTENT_TYPE_SSE in accept_hdr):
            logger.warning(
                f"Client rejected for session {channel_id}, bad Accept header: {accept_hdr}"
            )
            raise HTTPException(
                status_code=HTTPStatus.NOT_ACCEPTABLE,
                detail=f"Client must accept both {CONTENT_TYPE_JSON} and {CONTENT_TYPE_SSE}",
                headers={MCP_SESSION_ID_HEADER: channel_id} if channel_id else {}
            )

        # 2. Unsupported Media Type
        content_type_hdr = request.headers.get(CONTENT_TYPE_HEADER, "")
        if CONTENT_TYPE_JSON not in content_type_hdr:
            logger.warning(
                f"Client rejected for session {channel_id}, bad Content-Type header: {content_type_hdr}"
            )
            raise HTTPException(
                status_code=HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
                detail=f"Content-Type must be {CONTENT_TYPE_JSON}",
                headers={MCP_SESSION_ID_HEADER: channel_id} if channel_id else {}
            )

        return await call_next(request)
