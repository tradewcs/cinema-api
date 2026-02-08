from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

    APP_NAME: str = "online-cinema"
    DEBUG: bool = False

    BASE_URL: str

    EMAIL_HOST: str
    EMAIL_PORT: int
    EMAIL_HOST_USER: str
    EMAIL_HOST_PASSWORD: str
    EMAIL_USE_TLS: bool

    S3_STORAGE_HOST: str
    S3_STORAGE_PORT: int
    S3_STORAGE_ACCESS_KEY: str
    S3_STORAGE_SECRET_KEY: str
    S3_BUCKET_NAME: str

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

    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: str
    MINIO_HOST: str
    MINIO_PORT: int
    MINIO_STORAGE: str

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


settings = Settings()
