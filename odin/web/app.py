from fastapi import Depends, FastAPI, Request
from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware import Middleware

from core.config import settings
from web.middlewares.heimdall import CurrentUserMiddleware

MIDDLEWARE = [
    Middleware(BaseHTTPMiddleware, dispatch=CurrentUserMiddleware()),
]

app = FastAPI(
    title="Odin API",
    version="1.0.0",
    middleware=MIDDLEWARE,
    debug=settings.DEBUG,
    docs_url="/docs/",
    redoc_url="/redoc/",
)

mcp = FastMCP("Odin MCP", debug=settings.DEBUG)


app.mount(
    "/mcp",
    mcp.sse_app(),
    name="mcp",
)