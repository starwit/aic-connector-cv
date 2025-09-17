from pydantic import AnyHttpUrl, BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Annotated
from visionlib.pipeline.settings import LogLevel, YamlConfigSettingsSource
import pathlib
from typing import List, Optional, Optional

class MinioConfig(BaseModel):
    endpoint: str
    user: str
    password: str
    bucket_name: str
    secure: bool

class RedisInputConfig(BaseModel):
    host: str = 'localhost'
    port: Annotated[int, Field(ge=1, le=65536)] = 6379
    stream_ids: List[str]
    stream_prefix: str
    
class AuthConfig(BaseModel):
    token_endpoint_url: AnyHttpUrl
    client_id: str
    username: str
    password: str

class HttpOutputConfig(BaseModel):
    target_endpoint: AnyHttpUrl
    timeout: Annotated[int, Field(ge=0)] = 5
    module_name: str
    auth: Optional[AuthConfig] = None
    minio: MinioConfig

class LocalOutputConfig(BaseModel):
    path: pathlib.Path

class AicConnectorConfig(BaseSettings):
    log_level: LogLevel = LogLevel.WARNING
    redis_input: RedisInputConfig
    http_output: Optional[HttpOutputConfig] = None
    prometheus_port: Annotated[int, Field(ge=1024, le=65536)] = 8000
    local_output: Optional[LocalOutputConfig] = None    

    model_config = SettingsConfigDict(env_nested_delimiter='__')

    @classmethod
    def settings_customise_sources(cls, settings_cls, init_settings, env_settings, dotenv_settings, file_secret_settings):
        return (init_settings, env_settings, YamlConfigSettingsSource(settings_cls), file_secret_settings)