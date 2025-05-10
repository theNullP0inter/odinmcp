# Loki (MCP Inspector)

Loki is the integrated MCP Inspector UI for Asgard. It lets you browse and stream Model Context Protocol (MCP) events over Server-Sent Events (SSE) in real time.

## Features

- Bundles `@modelcontextprotocol/inspector` as a Docker service  
- Exposes a web UI on port `6274`  
- Connects to your organization’s SSE endpoint for live event debugging  

## Connecting to an MCP Endpoint

1. In the Loki UI, select **SSE** as the transport type.  
2. Enter your SSE URL, for example:

   ```
   http://localhost:8000/api/v1/{org_alias}/sse
   ```

   Replace `{org_alias}` with your organization alias (e.g. `org-1`).  
3. Click **Connect**. Events will stream live as they occur in OdinMCP.
