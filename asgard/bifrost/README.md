# Bifrost - API Gateway for Asgard

Bifrost is the API Gateway component in the Asgard distributed architecture. It is responsible for routing, securing, and orchestrating HTTP(S) traffic between clients and backend services such as Heimdall (authentication), Odin/OdinMCP (context protocol server), and others. Bifrost is built on top of [Kong Gateway](https://konghq.com) and leverages Kong’s plugin ecosystem for authentication, authorization, and cross-origin resource sharing.



## Key Features

- **Centralized API Gateway:**  
  Directs all incoming traffic to the appropriate microservice in the Asgard ecosystem.

- **OIDC Authentication:**  
  Uses the [Kong OIDC plugin](https://github.com/revomatico/kong-oidc) to enforce and validate OpenID Connect-based authentication, integrating with the Heimdall (Keycloak) identity provider.

- **CORS Support:**  
  Configures CORS (Cross-Origin Resource Sharing) for API endpoints to support browser-based tools (including mcp-inspector) and applications.

- **Transparent Routing:**  
  Exposes logical paths for services (e.g., `/heimdall/`, `/api/v1/`) while hiding internal network details.

- **OpenID Configuration Redirection:**  
  Handles special OIDC discovery endpoints for compatibility with MCP and LLM clients.



## Architecture

```
(Client)
   |
   v
[Bifrost (Kong Gateway)]
   |           |           |
  /            |            \
Heimdall    Odin/OdinMCP   OIDC Well-Known Redirect
(Auth)      (Core MCP)     (for OIDC Discovery)
```

- **Heimdall**: Authentication and organization management (`/heimdall/`)
- **Odin/OdinMCP**: MCP endpoints and real-time event streaming (`/api/v1/`)
- **OIDC Well-Known Redirect**: Ensures MCP clients discover the correct OpenID Provider configuration at `/.well-known/oauth-authorization-server`



## Route and Plugin Configuration

### 1. Heimdall Service

- **Route:** `/heimdall/` → Heimdall service (`http://heimdall:8080`)
- **CORS Plugin:** Allows all origins and common HTTP methods to support browser-based requests.

### 2. Odin/OdinMCP Service

- **Route:** `/api/v1/` → Odin service (`http://odin:80`)
- **OIDC Plugin:**  
  - Handles authentication using the `bifrost` client in Heimdall/Keycloak.
  - Validates tokens and ensures only authorized requests reach Odin.
  - Configuration includes discovery and introspection endpoints for the `asgard` realm.
- **CORS Plugin:**  
  - Supports all origins and standard methods for flexibility.

### 3. OIDC Well-Known Redirect

- **Route:** `/.well-known/oauth-authorization-server` → Heimdall OIDC config endpoint
- **Purpose:**  
  - MCP expects the OpenID configuration to be available at this path.
  - Bifrost rewires the path to Heimdall’s well-known OpenID endpoint for seamless OIDC discovery.
- **CORS Plugin:**  
  - Ensures clients from any origin can access the discovery endpoint.



## Example Kong Declarative Config

See [`config.yml`](../.conf.example/bifrost/config.yml) for a full example:

```yaml
_format_version: "3.0"
_transform: true

services:
  # Heimdall, Odin, and OIDC well-known routes as described above...
```



## Authentication Flow

1. **Incoming Client Request:**  
   Request arrives at Bifrost on a path such as `/api/v1/`.
2. **OIDC Validation:**  
   Kong OIDC plugin checks for a valid OIDC token (issued by Heimdall/Keycloak).
3. **Token Introspection:**  
   Plugin verifies token validity and fetches user info from Heimdall.
4. **Routing:**  
   On success, request is forwarded to Odin/OdinMCP with appropriate user context. Otherwise, access is denied.



## CORS Support

All routes are configured with a permissive CORS plugin. This is required for:

- Browser-based clients (e.g., [mcp-inspector](https://github.com/modelcontextprotocol/inspector))
- Developer tools and API testers



## Running Bifrost

Bifrost is launched as part of the Asgard stack via Docker Compose. Example:

```bash
docker-compose up bifrost
```

Ensure that:
- Heimdall and Odin services are running and accessible to Bifrost.
- OIDC client and secrets in the config are correct and match those set up in Heimdall/Keycloak.



## Security Notes

- **OIDC Client Secrets:**  
  Replace `REPLACE_WITH_A_SECRET_STRING` with a strong, secure value for production deployments.
- **CORS:**  
  While CORS is set to allow all origins for ease of development and integration, consider restricting origins in production.
