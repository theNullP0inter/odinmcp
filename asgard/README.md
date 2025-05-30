# Asgard

Asgard provides infrastructure to run [OdinMCP](https://github.com/odinmcp/odinmcp) in a distributed environment. This project integrates several open source components to provide authentication, API gateway management, efficient streaming, and a standardized way to connect large language models (LLMs) with data sources.

![Asgard Architecture Diagram](../docs/images/architecture.jpg)


## Key Components

- **Authentication and Authorization:** Managed via [Keycloak](https://www.keycloak.org) with OIDC protocols.

- **API Gateway:** Routes incoming requests to the appropriate service using [Kong Gateway](https://konghq.com) with the [Kong OIDC Plugin](https://github.com/revomatico/kong-oidc).

- **Streaming/SSE:** Handles server-sent events and real-time streaming via [Pushpin](https://pushpin.org) and the [GRIP Protocol](https://pushpin.org/docs/protocols/grip/).


### Authentication

- **Architecture:**  
  Authentication is managed by Keycloak and facilitated by Kong Gateway using OIDC protocols. Each service delegates authentication tasks to specialized systems.

- **Flow:**  
  1. The Bifrost gateway receives a request and extracts the token.
  2. It exchanges the token with the Heimdall service to validate and obtain user details.
  3. Validated user information is cached in memory and shared with downstream services.


### Streaming

- **Flow:**  
  1. A client request (e.g., to `mcp_endpoint`) that requires Server-Sent Events (SSE) is first routed to Hermod.
  2. Hermod forwards the request to the Bifrost gateway, adding a header to indicate SSE is expected.
  3. The server acknowledges the request and assigns a dedicated channel, which Hermod keeps open—offloading connection management from both the server and Bifrost.
  4. When the server needs to send events to the client, it publishes them to Hermod (typically via ZeroMQ).
  5. Hermod then relays these events directly to the client.
  6. If the client needs to send data back to the server, it can make a POST request to the MCP server. This request is acknowledged by the server, pushed as a task, and the response will be sent back in the initial stream.

- **Solution:**  
  By leveraging the GRIP Protocol with Pushpin, Asgard efficiently manages real-time communication and significantly reduces connection overhead on core services.


## Services

### Heimdall (Auth Service)

- **Purpose:**  
  Heimdall, built on top of [Keycloak](https://www.keycloak.org), handles user authentication and authorization. It also manages client registration and white labelling of domains.
  
- **Key Features:**  
  - Secure user authentication and authorization.
  - Integration with Keycloak’s organization management.
  - Centralized client registration.


### Bifrost (API Gateway)

- **Purpose:**  
  Bifrost is the API gateway powered by [Kong Gateway](https://konghq.com). It directs incoming requests to the appropriate services and integrates with Heimdall for token validation.
  
- **Key Features:**  
  - OIDC-based authentication using Kong's OIDC plugin ([Kong OIDC Plugin](https://github.com/revomatico/kong-oidc)).
  - Efficient routing and redirection of API requests.
  - Seamless integration with backend services.


### Hermod (Streaming Reverse Proxy)

- **Purpose:**  
  Hermod serves as a dedicated reverse proxy for handling server-sent events (SSE) and streaming. It leverages [Pushpin](https://pushpin.org) and the [GRIP Protocol](https://pushpin.org/docs/protocols/grip/) to support real-time data streaming.
  
- **Key Features:**  
  - Optimized for streaming and SSE.
  - Offloads streaming responsibilities from the MCP server and Bifrost.
  - Uses [ZeroMQ](https://zeromq.org) for scalable, distributed deployment.



### Loki (MCP Inspector)

- **Purpose:**  
  Loki hosts the MCP Inspector UI so you can browse and stream events via SSE.

- **Key Features:**  
  - Bundles `@modelcontextprotocol/inspector` as a Docker service  
  - Exposes a web UI on port `6274`  
  - Connects to your org’s SSE endpoint for live event debugging



## Acknowledgements

- [Keycloak](https://www.keycloak.org)
- [Kong Gateway](https://konghq.com)
- [Kong OIDC Plugin](https://github.com/revomatico/kong-oidc)
- [Pushpin](https://pushpin.org)
- [GRIP Protocol Documentation](https://pushpin.org/docs/protocols/grip/)
- [ZeroMQ](https://zeromq.org)
- [Model Context Protocol](https://github.com/modelcontextprotocol/python-sdk)
- [Starlette](https://www.starlette.io)
- [Celery](https://docs.celeryproject.org)
