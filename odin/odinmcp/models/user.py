from pydantic import BaseModel, Field
from typing import Any, Dict, List
import jwt
import time
from odinmcp.config import settings

class Organization(BaseModel):
    id: str
    organization_code: str


class CurrentUser(BaseModel):
    user_id:str
    session_id: str = Field(..., alias="sid")
    scope: List[str] = Field(default_factory=list)
    
    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_info(cls, info:Dict[str,Any]):
        info["scope"] = info.get("scope", "").split(" ")
        return cls(
            **info
        )
        
        
    # method to create a streaming token for the user
    # {user_id + session_id + timestamp}
    def create_hermod_streaming_token(self) -> str:
        payload = {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "created_at": int(time.time()),
        }
        token = jwt.encode(payload, settings.hermod_streaming_token_secret, algorithm="HS256")
        return token
    
    # method to validate the token: 
    # check with jwt secret and also check if the user_id, session_id are valid
    
    def validate_hermod_streaming_token(self, token:str) -> bool:
        try:
            payload = jwt.decode(token, settings.hermod_streaming_token_secret, algorithms=["HS256"])
            if payload["user_id"] != self.user_id or payload["session_id"] != self.session_id:
                return False
            return True
        except Exception as e:
            return False