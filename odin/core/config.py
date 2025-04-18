from pydantic_settings import BaseSettings
from typing import List



class Settings(BaseSettings):
    CORS_WHITELIST: List[str]
    ALLOWED_HOSTS: List[str]
    ENV: str
    DEBUG: bool
    
    HEIMDALL_ADMIN_CLIENT_ID: str
    HEIMDALL_ADMIN_CLIENT_SECRET: str
    
    HEIMDALL_REALM: str = "asgard"
    HEIMDALL_API_HOST: str = "http://heimdall:8080"
    

settings = Settings()