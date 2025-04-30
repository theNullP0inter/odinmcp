from pydantic import BaseModel
from typing import Any, Dict, List


class User(BaseModel):
    id:str
    email:str
    name: str
    organization: List[str]

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_info(cls, info:Dict[str,Any]):
        return cls(
            **info
        )