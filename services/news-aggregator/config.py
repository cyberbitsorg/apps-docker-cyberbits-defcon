from typing import Literal
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    redis_url: str = "redis://localhost:6379"
    fetch_interval_minutes: int = 60
    log_level: str = "INFO"
    internal_secret: str = ""
    scorer_version: Literal["v1", "v2"] = "v1"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
