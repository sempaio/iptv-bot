from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_ENV: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me"
    ALLOWED_HOSTS: str = "*"
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "postgresql://iptv:iptv@localhost:5432/iptvbot"

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"

    # Xtream Codes
    XTREAM_HOST: Optional[str] = None
    XTREAM_USERNAME: Optional[str] = None
    XTREAM_PASSWORD: Optional[str] = None

    # Export
    EXPORT_BASE_URL: str = "http://localhost:8000"
    DEFAULT_EXPORT_PROFILE: str = "default"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
