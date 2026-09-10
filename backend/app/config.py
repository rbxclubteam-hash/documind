from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://documind:documind@localhost:5434/documind"
    analyzer_mode: Literal["demo", "openai"] = "demo"
    openai_api_key: str | None = None
    openai_model: str | None = None
    cors_origins: str = "http://localhost:3001"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
