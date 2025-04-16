from pydantic import BaseModel
from typing import Any, Dict


class BaseUser(BaseModel):
    id:str
    email:str
    name: str

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_info(cls, info:Dict[str,Any]):
        return cls(
            **info
        )
        
class CurrentUser(BaseUser):
    pass
