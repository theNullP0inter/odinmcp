import base64
import json
from typing import Type
from starlette.exceptions import HTTPException
from odinmcp.models.user import CurrentUser
from monitors.logging import logger
from odinmcp.config import settings
from starlette.requests import Request


class HeimdallCurrentUserMiddleware:
    
    async def __call__(self, request: Request, call_next):
        user_info_token = request.headers.get(settings.user_info_token)
        
        if user_info_token:
            try:
                # Decode the token from base64, then decode bytes to string, and load the JSON
                user_info_bytes = base64.b64decode(user_info_token)
                user_info_str = user_info_bytes.decode("utf-8")
                user_info = json.loads(user_info_str)
                
                user = CurrentUser.from_info(user_info)
                
            except Exception as e:
                logger.error("Error parsing user_info_token", extra={"user_info_token": user_info_token, "error": e})
                raise HTTPException(status_code=401, detail='Unauthorized')
        else:
            raise HTTPException(status_code=401, detail='Unauthorized')
            
        org_code = request.path_params[settings.organization_path_param]
        if org_code not in user.organizations:
            # NOTE: ideally should be 403 but raising a 401 to restart the login flow
            raise HTTPException(status_code=401, detail='Forbidden. User does not have access to this organization')
        
        request.state.current_user = user
        response = await call_next(request)
        return response