# Hermod

Hermod is the real-time streaming and Server-Sent Events (SSE) gateway within the Asgard infrastructure of the OdinMCP distributed system. It is responsible for managing live data streams between backend services and clients, enabling efficient, scalable, and reliable real-time communication.

## Role in Asgard / OdinMCP
- **Streaming Gateway:** Hermod handles all real-time streaming and SSE connections for the system, offloading connection management from core services.
- **Integration:** It acts as a bridge between backend event sources and clients, ensuring seamless delivery of live updates, notifications, and event streams.
- **Scalability:** By centralizing streaming logic, Hermod supports scaling out communication across distributed worker nodes.

## Technology
- **Pushpin:** Hermod is built on [Pushpin](https://pushpin.org), an open source proxy server for real-time web applications.
- **GRIP Protocol:** Utilizes the [GRIP protocol](https://pushpin.org/docs/protocols/grip/) to manage subscriptions and event delivery.

## Deployment
Hermod is containerized for easy deployment. The provided `Dockerfile` uses the official Pushpin image:

```dockerfile
FROM fanout/pushpin
```

To run Hermod with Docker:

```bash
docker build -t hermod .
docker run -p 5561:5561 -p 5562:5562 hermod
```

- By default, Pushpin listens on ports 5561 (HTTP) and 5562 (zmq).
- Configure Pushpin as needed for your environment (see [Pushpin docs](https://pushpin.org/docs/)).

## Integration & Usage
- Backend services publish events to Hermod using the GRIP protocol.
- Clients connect via SSE or WebSocket to receive real-time updates.
- Hermod is typically deployed alongside other Asgard components (Heimdall, Bifrost, Loki) to provide a complete, secure, and scalable distributed infrastructure.

## References
- [Pushpin Documentation](https://pushpin.org/docs/)
- [GRIP Protocol](https://pushpin.org/docs/protocols/grip/)

---
Hermod is a critical part of OdinMCP's distributed, real-time architecture, ensuring robust and scalable event streaming for modern AI and data applications.
