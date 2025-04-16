from pydantic_settings import BaseSettings
from typing import List



class Settings(BaseSettings):
    CORS_WHITELIST: List[str]
    ALLOWED_HOSTS: List[str]
    ENV: str
    DEBUG: bool
    
    HEIMDALL_REALM: str
    HEIMDALL_API_HOST: str
    HEIMDALL_ADMIN_CLIENT_ID: str
    HEIMDALL_ADMIN_CLIENT_SECRET: str
    

settings = Settings()