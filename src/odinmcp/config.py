from typing import Generic, Optional, List

from pydantic_settings import BaseSettings, SettingsConfigDict
from mcp.server.lowlevel.server import LifespanResultT


class OdenSettings(BaseSettings, Generic[LifespanResultT]):
    model_config = SettingsConfigDict(
        env_prefix="ODINMCP_",
        env_file=".env",
        env_nested_delimiter="__",
        nested_model_default_partial_update=True,
        extra="ignore",
    )
    
    
    # debugging
    debug: Optional[bool] = False
    
    
    
    # authentication and streaming
    user_info_token: Optional[str] = "x-userinfo"
    hermod_streaming_header: Optional[str] = "x-hermod-stream"
    hermod_streaming_token_secret: Optional[str] = "secret"
    hermod_zero_mq_urls: Optional[List[str]] = ["tcp://localhost:5562"]
    hermod_streaming_keep_alive_timeout: Optional[int] = 10
    
    
    # state variables
    current_user_state: Optional[str] = "current_user"
    supports_hermod_streaming_state: Optional[str] = "supports_hermod_streaming"
    
    # celery settngs
    celery_broker: Optional[str] = "redis://localhost:6379/0"
    celery_backend: Optional[str] = "redis://localhost:6379/0"
    
settings = OdenSettings()