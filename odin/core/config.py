from pydantic_settings import BaseSettings
from typing import List



class Settings(BaseSettings):


    ENV: str
    DEBUG: bool
    ROOT_PATH: str = "/"
    
    HEIMDALL_ADMIN_CLIENT_ID: str
    HEIMDALL_ADMIN_CLIENT_SECRET: str
    
    HEIMDALL_REALM: str = "asgard"
    HEIMDALL_API_HOST: str = "http://heimdall:8080"
    

settings = Settings()