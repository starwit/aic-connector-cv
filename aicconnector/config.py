from pydantic import AnyHttpUrl, BaseModel, Field, model_validator
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
    decision_type_names: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_decision_type_names(self):
        if self.decision_type_names:
            missing_streams = [
                stream_id
                for stream_id in self.stream_ids
                if not self.decision_type_names.get(stream_id, "").strip()
            ]
            if missing_streams:
                raise ValueError(
                    "Missing decision type names for streams: " + ", ".join(missing_streams)
                )
        return self
    
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

class AicConnectorConfig(BaseSettings):
    log_level: LogLevel = LogLevel.WARNING
    redis_input: RedisInputConfig
    http_output: Optional[HttpOutputConfig] = None
    prometheus_port: Annotated[int, Field(ge=1024, le=65536)] = 8000
    model_config = SettingsConfigDict(env_nested_delimiter='__')

    @classmethod
    def settings_customise_sources(cls, settings_cls, init_settings, env_settings, dotenv_settings, file_secret_settings):
        return (init_settings, env_settings, YamlConfigSettingsSource(settings_cls), file_secret_settings)
