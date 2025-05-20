from odinmcp.server.config import settings




class HermodStreamingMiddleware:
    async def __call__(self, request, call_next):
        hermod_header = request.headers.get(settings.hermod_streaming_header, "false")
        if hermod_header != "true" and "text/event-stream" in request.headers.get("Accept", ""):
            # TODOD: Find a better option. Replace "text/event-stream" part of the header with whatever is leaving the rest of the header intact
            request.headers["Accept"] = request.headers["Accept"].replace(
                "text/event-stream", "")
        response = await call_next(request)
        return response
