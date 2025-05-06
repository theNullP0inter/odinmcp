from pydantic import BaseModel
from typing import Any, Dict, List

class Organization(BaseModel):
    id: str
    organization_code: str


class User(BaseModel):
    user_id:str
    name: str
    email:str
    name: str
    organizations: Dict[str, Organization]

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_info(cls, info:Dict[str,Any]):
        mapped_orgs = {}
        for org_code, org in info.get("organization", {}).items():
            mapped_orgs[org_code] = Organization(
                id=org.get("id"),
                organization_code=org_code
            )
            
        info["organizations"] = mapped_orgs
        del info["organization"]
        
        print(f"User info: {info}")
        return cls(
            **info
        )