

class HermodStreamingMiddleware:
    async def __call__(self, request, call_next):
        hermod_header = request.headers.get("X-HERMOD-STREAM")
        request.state.supports_hermod_streaming = (hermod_header == "true")    
        response = await call_next(request)
        return response
