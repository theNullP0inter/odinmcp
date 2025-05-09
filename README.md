# Asgard

Asgard is an enterprise-level MCP implementation designed as a side project to explore and learn the possibilities of using MCPs in a distributed environment. This project integrates several open source components to provide authentication, API gateway management, efficient streaming using modern protocols, and a standardized framework for connecting large language models (LLMs) with context-aware data sources and tools through MCPs.

## Overview

Asgard leverages a microservices-based architecture to ensure scalability, resilience, and performance in distributed deployments. The project is an experimental implementation that combines the strengths of popular tools and platforms such as Keycloak, Kong Gateway, and Pushpin, while also emphasizing the use of Model Context Protocol (MCP) to seamlessly integrate context with LLMs.

## What is MCP?

Model Context Protocol (MCP) is an open standard that defines how applications can provide context to large language models (LLMs). Think of MCP as a USB-C port for AI applications—it offers a standardized way to connect your LLMs to different data sources and tools. 

### Why MCP?

MCP is crucial for building intelligent agents and orchestrating complex workflows on top of LLMs. LLMs often need to integrate with various data sources and external tools, and MCP provides the following benefits:
- **Pre-Built Integrations:** A growing list of integrations that allow your LLM to plug directly into various services.
- **Flexibility:** The ability to switch between different LLM providers and vendors without rewriting integration logic.
- **Security Best Practices:** Standardized practices to ensure that your data remains secure within your infrastructure.

### General Architecture of MCP

At its core, MCP uses a client-server architecture where a host application can connect to multiple servers. Asgard aims to expand this architecture for distributed systems, leveraging MCP to standardize context delivery across multiple services and nodes in a cloud environment.

Learn more about MCP on the [Model Context Protocol Python SDK](https://github.com/modelcontextprotocol/python-sdk).

## Problem Statement

The goal of Asgard is to address challenges in managing authentication, client registration, white labelling domains, high-demand streaming, and integrating scalable context delivery through MCP in a distributed ecosystem. By decoupling these concerns into dedicated services, Asgard provides:
- Secure user authentication and authorization.
- Efficient API routing and gateway management.
- Scalable streaming capabilities using the GRIP protocol.
- Standardized and flexible context communication for LLMs with MCP.

## Architecture

The overall architecture of Asgard is depicted in the diagram below:

![Architecture Diagram](./docs/architecture.jpg)

Key components include:
- **Microservice Control Plane (MCP):** Orchestrates the interaction between various services and integrates context for LLMs using the Model Context Protocol.
- **Authentication and Authorization:** Managed via Keycloak and OIDC protocols.
- **API Gateway:** Routes incoming requests to the appropriate service.
- **Streaming/SSE:** Handles server-sent events and real-time streaming with Pushpin and GRIP.
- **Context Delivery via MCP:** Enables standardized connectivity between LLMs and various data sources.

## Services

### Heimdall (Auth Service)

- **Purpose:**  
  Heimdall, built on top of Keycloak, handles user authentication and authorization. It also manages client registration and domain white labelling.
  
- **Key Features:**  
  - User authentication and authorization.
  - Organization management using Keycloak.
  - Centralized client registration.

### Bifrost (API Gateway)

- **Purpose:**  
  Bifrost functions as the API gateway, built on Kong Gateway, directing requests to the appropriate downstream services.
  
- **Key Features:**  
  - OIDC-based authentication via Kong’s OIDC plugin.
  - Integration with Heimdall for token validation.
  - Efficient API routing.

### Hermod (Streaming Reverse Proxy)

- **Purpose:**  
  Hermod is a dedicated reverse proxy for handling server-sent events (SSE) and streaming. It uses Pushpin and the GRIP protocol for real-time data streaming.
  
- **Key Features:**  
  - Optimized for streaming and SSE.
  - Offloads streaming responsibilities from the MCP server.
  - Utilizes ZeroMQ for distributed deployment.

## Authentication

- **Architecture:**  
  Authentication is managed by Keycloak and facilitated by Kong Gateway using OIDC protocols. This approach allows each service to offload authentication tasks to specialized systems.

- **Flow:**  
  1. The Bifrost gateway receives a request and extracts the token.
  2. It exchanges the token with the Heimdall service to validate and fetch user details.
  3. The validated user information is cached in memory and shared with downstream services for authorization checks.

## Streaming and Server-Sent Events (SSE)

- **Challenge:**  
  Traditional MCP-based SSE implementations are not optimal for distributed environments.

- **Solution:**  
  Asgard integrates the GRIP protocol with Pushpin to manage streaming. This design reduces the load on the MCP server while delivering a scalable real-time communication solution.

- **Implementation Details:**  
  - **Pushpin:** Handles HTTP streaming and WebSockets with support for numerous concurrent connections.
  - **GRIP Protocol:** Enables efficient routing of streaming data.
  - **ZeroMQ:** Facilitates the deployment and scaling of Pushpin across distributed nodes.

## Getting Started

Follow these steps to set up and run Asgard locally:

1. **Setup Environment:**
   Execute the setup script to configure and copy sample configuration and environment files.
   ```bash
   ./setup.sh
   ```

2. **Start Services:**
   Run Docker Compose to launch all necessary services.
   ```bash
   docker-compose up
   ```

3. **Run the Inspector:**
   Use the Model Context Protocol inspector to run checks and integrations.
   ```bash
   npx @modelcontextprotocol/inspector
   ```

## Roadmap

Planned future enhancements for Asgard include:

- **Authentication Enhancements:**  
  Further improvements in authentication processes and service integrations.
  
- **Streaming Improvements:**  
  Optimizing streaming capabilities to support additional protocols and higher concurrency.
  
- **OdinMCP Python Library:**  
  Developing a unified Python library to abstract MCP complexities and other Asgard implementations for easier integration.

## Contributing

Contributions to Asgard are welcome! Please open issues, fork the repository, and submit pull requests to improve functionality and performance.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Keycloak](https://www.keycloak.org/)
- [Kong Gateway](https://konghq.com/)
- [Pushpin](https://pushpin.org/)
- [GRIP Protocol](https://pushpin.org/docs/protocols/grip/)
- [ZeroMQ](https://zeromq.org/)
- [Model Context Protocol](https://github.com/modelcontextprotocol/python-sdk)

Happy coding and exploring the distributed environment with Asgard!
