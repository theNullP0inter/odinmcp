# Asgard

Asgard provides infrasturcture to run [OdinMCP](https://github.com/odinmcp/odinmcp) in a distributed environment. This project integrates several open source components to provide authentication, API gateway management, efficient streaming, and a standardized way to connect large language models (LLMs) with data sources.





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


### Streaming and Server-Sent Events (SSE)

- **Flow:**  
  1. A request that supports SSE is first directed to Hermod with a header indicating SSE support.
  2. Hermod forwards the request through Bifrost, which routes it to the necessary service/API/MCP.
  3. The server acknowledges the request and responds with a `messages_endpoint` along with GRIP headers, instructing Hermod to hold the connection.
  4. This process offloads the connection management from both the server and Bifrost.
  5. Events can then be published to Hermod either via ZeroMQ or by calling the `/publish` endpoint on Hermod.

- **Solution:**  
  By integrating the GRIP Protocol with Pushpin, Asgard effectively manages real-time communications and minimizes connection overhead on core services.


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


### OdinMCP

**OdinMCP** is the core Model Context Protocol (MCP) controller in Asgard, built with [FastAPI](https://fastapi.tiangolo.com) and the [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk). It acts as the control plane for managing context delivery, event streaming, and coordination between microservices and LLMs.

#### Key Responsibilities

- Central hub for context communication between services, LLMs, and clients.
- Provides endpoints for sending, receiving, and streaming context/messages.
- Handles session management, message publication, and event broadcasting.
- Integrates with authentication (Heimdall/Keycloak), API gateway (Bifrost/Kong), and Hermod/Pushpin for SSE streaming.
- Coordinates with Odin Workers (Celery) and Redis for background processing and event queuing.

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
- [FastAPI](https://fastapi.tiangolo.com)