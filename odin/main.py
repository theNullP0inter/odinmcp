from odinmcp import OdinMCP
from fastapi import FastAPI



mcp = OdinMCP(
    "Odin MCP", 
    "easy way to fetch all your data"
)


web = mcp.get_web()
celery = mcp.get_worker()

