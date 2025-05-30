# Loki (MCP Inspector)

Loki is the integrated MCP Inspector UI for Asgard. It lets you browse and stream Model Context Protocol (MCP) events over HTTP Streaming in real time.

## Features

- Bundles `@modelcontextprotocol/inspector` as a Docker service  
- Exposes a web UI on port `6274`  
- Connects to your HTTP Streaming MCP endpoint for live event debugging  

## Connecting to an MCP Endpoint

1. In the Loki UI, select **Streamable HTTP** as the transport type.  
2. Enter your HTTP Streaming URL, for example:

   ```
   http://localhost:8000/api/v1/
   ```

3. Click **Connect**. Events will stream live as they occur in OdinMCP.
