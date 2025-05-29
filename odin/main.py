from odinmcp import OdinMCP
from fastapi import FastAPI
from mcp.server.fastmcp import Context


mcp = OdinMCP("Odin MCP Demo")

@mcp.tool()
def add(a: int, b: int) -> int:
    return a + b

@mcp.tool()
async def get_roots(ctx: Context) -> list[str]:
    return await ctx.session.list_roots()


web, worker = mcp.sse_app()

