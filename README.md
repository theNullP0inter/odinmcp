# Asgard

Asgard is an enterprise-level MCP implementation designed as a side project to explore and learn the possibilities of using MCPs in a distributed environment. This project integrates several open source components to provide authentication, API gateway management, efficient streaming, and a standardized way to connect large language models (LLMs) with data sources.

## Overview

Asgard leverages a microservices-based architecture to ensure scalability, resilience, and performance in distributed deployments. This experimental implementation combines the strengths of popular open source tools to deliver a robust distributed application framework.

## What is MCP?

Model Context Protocol (MCP) is an open protocol that standardizes how applications provide context to LLMs. In Asgard, MCP facilitates communication between services and LLMs by offering a standardized channel for context delivery.  
Learn more about MCP on the [Model Context Protocol Python SDK](https://github.com/modelcontextprotocol/python-sdk).

## Problem Statement

The goal of Asgard is to address challenges related to securing user authentication, managing client registration and white labelling domains, handling high-demand streaming, and standardizing context communication for LLMs in a distributed ecosystem.

## Architecture

The overall architecture of Asgard is depicted below:

![Architecture Diagram](./docs/architecture.jpg)

Key components include:
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

- **Purpose:**  
  OdinMCP is a basic implementation of an MCP built on [FastAPI](https://fastapi.tiangolo.com) using the mcp Python library. It serves as the foundational control plane for managing interactions among microservices in Asgard.
  
- **Key Features:**  
  - Provides a simple, out-of-the-box MCP setup.
  - Facilitates context delivery between services and LLMs.
  - Will later be refactored and extracted into its own client library to further abstract MCP complexities and simplify integrations.



## Getting Started

Follow these steps to set up and run Asgard on your local machine:

1. **Setup Environment:**
   Execute the setup script to prepare sample configuration and environment files.
   ```bash
   ./setup.sh
   ```

2. **Start Services:**
   Use Docker Compose to launch all required services.
   ```bash
   docker-compose up
   ```

3. **Run the Inspector:**
   Execute the MCP inspector to verify integrations.
   ```bash
   npx @modelcontextprotocol/inspector
   ```

## Roadmap

Future enhancements for Asgard include:

- ~~**Authentication Enhancements:**  
  Further improvements in auth processes and service integrations.~~
  
- **Streaming Improvements:**  
  Optimizing streaming capabilities for additional protocols and higher concurrency.
  
- **OdinMCP Python Library:**  
  Refactoring OdinMCP into its own client library to better abstract MCP complexities and simplify integrations.

## Contributing

Contributions to Asgard are welcome! Please open issues, fork the repository, and submit pull requests to help improve functionality and performance.

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.

## Acknowledgements

- [Keycloak](https://www.keycloak.org)
- [Kong Gateway](https://konghq.com)
- [Kong OIDC Plugin](https://github.com/revomatico/kong-oidc)
- [Pushpin](https://pushpin.org)
- [GRIP Protocol Documentation](https://pushpin.org/docs/protocols/grip/)
- [ZeroMQ](https://zeromq.org)
- [Model Context Protocol](https://github.com/modelcontextprotocol/python-sdk)
- [FastAPI](https://fastapi.tiangolo.com)

Happy coding and exploring the distributed environment with Asgard!
