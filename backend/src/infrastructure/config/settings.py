from functools import lru_cache
from typing import Annotated, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Gemelo Digital Huancayo API"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://digital_twin:change_me@localhost:5432/digital_twin"
    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    mqtt_enabled: bool = False
    data_root: str = "data"
    core_repository: Literal["memory", "sqlalchemy"] = "memory"
    demo_repository: Literal["memory", "sqlalchemy"] = "memory"
    demo_ml_metadata_path: str = "ml/models/demo_peru/metadata.json"
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]
    log_level: str = "INFO"
    ml_model_path: str = "../ml/models/traffic_model.joblib"
    sumo_binary: str = "sumo"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors_origins(cls, value: object) -> object:
        if isinstance(value, str) and not value.startswith("["):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
