from functools import lru_cache
from typing import Annotated, Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Gemelo Digital Huancayo API"
    environment: str = "development"
    database_url: str = (
        "postgresql+psycopg://digital_twin:change_me@localhost:5432/digital_twin"
    )
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

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_postgres_url(cls, value: object) -> object:
        """Map provider-issued Postgres URLs to the installed psycopg v3 driver."""
        if isinstance(value, str):
            if value.startswith("postgres://"):
                return "postgresql+psycopg://" + value[len("postgres://"):]
            if value.startswith("postgresql://"):
                return "postgresql+psycopg://" + value[len("postgresql://"):]
        return value

    @model_validator(mode="after")
    def validate_cloud_settings(self) -> "Settings":
        if self.environment == "staging":
            if self.core_repository != "sqlalchemy" or self.demo_repository != "sqlalchemy":
                raise ValueError("Staging requires SQLAlchemy repositories.")
            if not self.database_url.startswith("postgresql+psycopg://"):
                raise ValueError("Staging requires a PostgreSQL URL using psycopg.")
            if any(
                host in self.database_url
                for host in ("@localhost:", "@127.0.0.1:", "@postgres:")
            ):
                raise ValueError("Staging needs a remote PostgreSQL host.")
            if not self.cors_origins or any(
                not origin.startswith("https://") for origin in self.cors_origins
            ):
                raise ValueError("Staging requires an HTTPS frontend CORS origin.")
        return self

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors_origins(cls, value: object) -> object:
        if isinstance(value, str) and not value.startswith("["):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
