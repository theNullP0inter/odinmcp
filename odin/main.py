from odinmcp import OdinMCP
from fastapi import FastAPI



mcp = OdinMCP("Odin MCP Demo")

@mcp.tool()
def add(a: int, b: int) -> int:
    return a + b


web, worker = mcp.sse_app()

