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



## Getting Started with Asgard

This guide will walk you through setting up and running Asgard on your local machine.

---

### 1. Setup Environment

Prepare your local environment by running the setup script. This script creates sample configuration and environment files needed for Asgard.

```bash
./setup.sh
```

---

### 2. Start Services

Launch all required services using Docker Compose:

```bash
docker-compose up
```

---

### 3. Configure Keycloak

Keycloak is used as the identity provider. Follow these steps to configure it:

#### a. Access the Admin Console

1. Open your browser and navigate to:  
   `http://localhost:8000/heimdall/`
2. Log in with the following admin credentials:
   - **Username:** `admin`
   - **Password:** `adminpassword`

#### b. Verify Pre-Configured Settings

- A sample realm named `asgard` should already exist.
- The necessary sample clients have been pre-configured within the realm.

#### c. Create a New Organization and User

1. **Create Organization:**  
   Within the `asgard` realm, create a new organization. For example, name it `org-1`.

   ![Create Organization](./docs/create_org.png)

2. **Create User:**  
   Create a new user in the realm and assign the user to the newly created organization `org-1`.

   ![Create User](./docs/create_user.png)

3. **Set User Credentials:**  
   Ensure the new user sets secure credentials.

   ![Set User Credentials](./docs/set_user_creds.png)

4. **Assign User to Organization:**  
   Add the user to the `org-1` organization.

   ![Add User to Organization](./docs/add_user_to_org.png)

> **Note:** The initial setup of Heimdall might take some time as it runs initial migrations.

---

### 4. Run the MCP Inspector

To verify integrations, run the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector
```

Then, open the inspector in your browser:
[http://localhost:6274/](http://localhost:6274/)

---

### 5. Connect to the OdinMCP Server Using the Inspector

Follow these steps to connect to the MCP server for your organization (`org-1`):

1. In the inspector, change the transport type to **SSE**.
2. Enter the following URL:

   ```
   http://localhost:8000/api/v1/mcp/org-1/sse
   ```

   This URL connects to the `org-1` organization's MCP endpoint and starts streaming events. Make sure to use the correct organization alias.

#### Connection Steps

- **Enter SSE Endpoint:**  
  ![Enter SSE Endpoint](./docs/connect_sse_1.png)

- **Login Prompt:**  
  ![Login](./docs/connect_sse_2.png)

- **Grant Access to MCP Client:**  
  ![Grant Access to MCP Client](./docs/connect_sse_3.png)

- **Successful Connection:**  
  ![Connected](./docs/connect_sse_4.png)

   

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
