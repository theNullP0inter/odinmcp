from pydantic_settings import BaseSettings
from typing import List



class Settings(BaseSettings):

    ENV: str
    DEBUG: bool
    ROOT_PATH: str = "/"
    

settings = Settings()