from odinmcp import OdinMCP
from fastapi import FastAPI



mcp = OdinMCP(
    "Odin MCP", 
    "easy way to fetch all your data"
)


web = mcp.sse_app()
celery = mcp.async_worker()

