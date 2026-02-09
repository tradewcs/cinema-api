from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

    BASE_DIR: str = str(Path(__file__).resolve().parent.parent)

    APP_NAME: str = "online-cinema"
    DEBUG: bool = False

    BASE_URL: str

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int

    JWT_ACCESS_TTL: int
    JWT_REFRESH_TTL: int
    SECRET_KEY: str

    REDIS_HOST: str
    REDIS_PORT: int

    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


settings = Settings()
