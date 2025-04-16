import base64
import json
from typing import Type

import jwt

from models.user import CurrentUser
from monitors.logging import logger



class CurrentUserMiddleware:
        
    async def __call__(self, request, call_next):
        auth_token = request.headers.get("authorization")
        access_token = auth_token.split(" ")[1] if auth_token else None
        
        if access_token:
            try:
                user_info = jwt.decode(
                    access_token, 
                    options={"verify_signature": False}
                )
                request.state.user = CurrentUser.from_info(
                    user_info
                )
            except Exception as e:
                logger.error(f"Error parsing access_token", extra={"access_token": access_token, "error":e})
                request.state.user = None
        else:
            request.state.user = None
            
        response = await call_next(request)
        return response
