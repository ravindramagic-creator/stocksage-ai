from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Existing application settings
    APP_NAME: str = "StockSage AI"
    APP_VERSION: str = "1.0.0"

    # Database
    DATABASE_URL: str = "sqlite:///./stocksage.db"

    # ---------------------------------------------------------
    # IndianAPI
    # ---------------------------------------------------------
    INDIANAPI_API_KEY: str | None = None

    INDIANAPI_BASE_URL: str = "https://stock.indianapi.in"

    # ---------------------------------------------------------
    # Keep unknown .env variables from crashing startup.
    # This is important because you previously had
    # ALPHAVANTAGE_API_KEY in .env.
    # ---------------------------------------------------------
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
