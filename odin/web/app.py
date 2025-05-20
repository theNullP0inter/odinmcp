from fastapi import Depends, FastAPI, Request
from odinmcp.server.odinmcp import OdinMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware import Middleware

from core.config import settings


app = FastAPI(
    title="Odin API",
    version="1.0.0",
    debug=settings.DEBUG,
    docs_url="/docs/",
    redoc_url="/redoc/",
)

mcp = OdinMCP("Odin MCP", "easy way to fetch all your data", debug=settings.DEBUG)



app.mount(
    "/mcp",
    mcp.app(),
    name="mcp",
)
