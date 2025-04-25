"""
Configuration settings for the Data Dictionary Agency application.
"""
import os
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application settings
    PROJECT_NAME: str = "Data Dictionary Agency"
    PROJECT_DESCRIPTION: str = "Automated data dictionary generation for GitHub repositories"
    VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_PREFIX: str = "/api"
    SECRET_KEY: str = "development-secret-key"

    # CORS settings
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # PostgreSQL settings
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "dda"

    # MongoDB settings
    MONGODB_URI: str = "mongodb://localhost:27017/dda"

    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # GitHub settings
    GITHUB_TOKEN: str = ""
    GITHUB_API_URL: str = "https://api.github.com"

    # Format detection settings
    DEFAULT_CONFIDENCE_THRESHOLD: float = 0.7
    MAX_FILE_SIZE_MB: int = 100
    ENABLE_STREAMING_PROCESSING: bool = True

    # Processing settings
    MAX_WORKERS: int = 4
    CHUNK_SIZE: int = 10000

    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Database connection URLs
    @property
    def postgres_dsn(self) -> str:
        """Generate the PostgreSQL connection URL."""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def redis_url(self) -> str:
        """Generate the Redis connection URL."""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Pydantic settings configuration
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )


# Create settings instance
settings = Settings()
