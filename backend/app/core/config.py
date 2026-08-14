from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "StockSage AI"
    API_VERSION: str = "v1"
    DATABASE_URL: str = "sqlite:///./stocksage.db"

    class Config:
        env_file = ".env"


settings = Settings()
