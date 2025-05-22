from odinmcp.odinmcp import OdinMCP



mcp = OdinMCP(
    "Odin MCP", 
    "easy way to fetch all your data"
)


web = mcp.sse_app()
celery = mcp.worker()

