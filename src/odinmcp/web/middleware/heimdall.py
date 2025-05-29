import base64
import json
from typing import Type
from starlette.exceptions import HTTPException
from odinmcp.models.auth import CurrentUser

from odinmcp.config import settings
from starlette.requests import Request


class HeimdallCurrentUserMiddleware:
    def __init__(self, user_model: Type[CurrentUser]):
        self.user_model = user_model
    
    async def __call__(self, request: Request, call_next):
        user_info_token = request.headers.get(settings.user_info_token)
        
        if user_info_token:
            try:
                # Decode the token from base64, then decode bytes to string, and load the JSON
                user_info_bytes = base64.b64decode(user_info_token)
                user_info_str = user_info_bytes.decode("utf-8")
                user_info = json.loads(user_info_str)
                
                user = self.user_model.from_info(user_info)
                
            except Exception as e:
                raise HTTPException(status_code=401, detail='Unauthorized')
        else:
            raise HTTPException(status_code=401, detail='Unauthorized')
            
        
        setattr(request.state, settings.current_user_state, user)
        response = await call_next(request)
        return response
    
