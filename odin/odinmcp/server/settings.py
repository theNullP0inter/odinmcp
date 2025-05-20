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
    debug: Optional[bool] = False
    path_prefix: Optional[str] = "mcp"
    organization_path_param: Optional[str] = "org_code"
    

