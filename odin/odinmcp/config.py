from typing import Generic, Optional

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
    hermod_streaming_token_secret: str
    
    
    # state variables
    current_user_state: Optional[str] = "current_user"
    supports_hermod_streaming_state: Optional[str] = "supports_hermod_streaming"

settings = OdenSettings()