import base64
import json
from typing import Type

from models.user import User
from monitors.logging import logger

class CurrentUserMiddleware:
    
    async def __call__(self, request, call_next):
        user_info_token = request.headers.get("x-userinfo")
        
        if user_info_token:
            try:
                # Decode the token from base64, then decode bytes to string, and load the JSON
                user_info_bytes = base64.b64decode(user_info_token)
                user_info_str = user_info_bytes.decode("utf-8")
                user_info = json.loads(user_info_str)
                
                request.state.user = User.from_info(user_info)
            except Exception as e:
                logger.error("Error parsing user_info_token", extra={"user_info_token": user_info_token, "error": e})
                request.state.user = None
        else:
            request.state.user = None
            
        response = await call_next(request)
        return response