import base64
import json
from typing import Type
from starlette.exceptions import HTTPException
from models.user import User
from monitors.logging import logger
from odinmcp.server.config import settings
from starlette.requests import Request


class CurrentUserMiddleware:
    
    async def __call__(self, request: Request, call_next):
        user_info_token = request.headers.get(settings.user_info_token)
        
        if user_info_token:
            try:
                # Decode the token from base64, then decode bytes to string, and load the JSON
                user_info_bytes = base64.b64decode(user_info_token)
                user_info_str = user_info_bytes.decode("utf-8")
                user_info = json.loads(user_info_str)
                
                user = User.from_info(user_info)
                
            except Exception as e:
                logger.error("Error parsing user_info_token", extra={"user_info_token": user_info_token, "error": e})
                raise HTTPException(status_code=401, detail='Unauthorized')
        else:
            raise HTTPException(status_code=401, detail='Unauthorized')
            
        # request.path_params[settings.organization_path_param]
        logger.info(" url:", extra={"url": request.url})
        logger.info(" path_params", extra={"path_params": request.path_params})
        org_code = request.path_params[settings.organization_path_param]
        if org_code not in user.organizations:
            # NOTE: ideally should be 403 but raising a 401 to restart the login flow
            raise HTTPException(status_code=401, detail='Forbidden. User does not have access to this organization')
        response = await call_next(request)
        return response