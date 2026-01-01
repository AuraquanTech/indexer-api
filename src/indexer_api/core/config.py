"""
Application configuration using pydantic-settings.
Supports environment variables and .env files.
"""
from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "IndexerAPI"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"

    # API
    api_prefix: str = "/api/v1"
    allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4

    # Database
    database_url: str = "sqlite+aiosqlite:///./indexer.db"
    database_echo: bool = False
    database_pool_size: int = 5
    database_max_overflow: int = 10

    # PostgreSQL (for production)
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "indexer"
    postgres_password: str = "indexer_secret"
    postgres_db: str = "indexer_db"

    @computed_field
    @property
    def postgres_dsn(self) -> str:
        """Build PostgreSQL connection string."""
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl: int = 3600  # 1 hour

    # Authentication
    secret_key: str = "CHANGE-THIS-IN-PRODUCTION-use-openssl-rand-hex-32"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    def model_post_init(self, __context) -> None:
        """Validate settings after initialization."""
        # Fail in production with default secret key
        if self.environment == "production":
            if self.secret_key == "CHANGE-THIS-IN-PRODUCTION-use-openssl-rand-hex-32":
                raise ValueError(
                    "CRITICAL: You must set a secure SECRET_KEY in production! "
                    "Generate one with: openssl rand -hex 32"
                )

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds

    # Indexing
    max_concurrent_jobs: int = 5
    max_file_size_mb: int = 100
    index_chunk_size: int = 1000
    supported_extensions: list[str] = Field(
        default_factory=lambda: [".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c", ".h"]
    )

    # Storage
    storage_backend: Literal["local", "s3"] = "local"
    storage_path: str = "./data/indexes"
    s3_bucket: str = ""
    s3_region: str = "us-east-1"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # Logging
    log_level: str = "INFO"
    log_format: Literal["json", "console"] = "console"

    # Billing (Stripe)
    stripe_api_key: str = ""
    stripe_webhook_secret: str = ""

    # Feature Flags
    enable_vector_search: bool = True
    enable_semantic_analysis: bool = False
    enable_billing: bool = False

    # DAM - Digital Asset Management
    enable_dam: bool = True
    dam_thumbnail_size: tuple[int, int] = (200, 200)
    dam_extract_colors: bool = True
    dam_max_colors: int = 5

    # Code Discovery
    enable_code_discovery: bool = True
    code_max_file_size_kb: int = 500
    code_languages: list[str] = Field(
        default_factory=lambda: ["python", "javascript", "typescript", "go", "rust", "java", "c", "cpp"]
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience alias
settings = get_settings()
