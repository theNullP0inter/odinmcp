from odinmcp import OdinMCP
from fastapi import FastAPI
from mcp.server.fastmcp import Context
import time

mcp = OdinMCP("Odin MCP Demo")

@mcp.tool()
def add(a: int, b: int) -> int:
    return a + b

@mcp.tool()
async def send_client_request_for_roots(ctx: Context) -> list[str]:
    return await ctx.session.list_roots()

@mcp.tool()
async def very_long_running_task_will_cancel(ctx: Context) -> None:
    print("very_long_running_task_will_cancel has started")
    time.sleep(30)
    print("very_long_running_task_will_cancel has finished")



web, worker = mcp.sse_app()

