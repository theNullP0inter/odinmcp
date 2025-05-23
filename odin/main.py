from odinmcp import OdinMCP
from fastapi import FastAPI



mcp = OdinMCP("Odin MCP Demo")


web, worker = mcp.sse_app()

