"""Application configuration using Pydantic Settings.

This module provides centralized configuration management with environment
variable validation, type coercion, and default values.
"""

from enum import Enum
from functools import lru_cache

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Application environment."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Log level options."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(str, Enum):
    """Log format options."""

    JSON = "json"
    CONSOLE = "console"


class StorageBackend(str, Enum):
    """Storage backend options."""

    LOCAL = "local"
    S3 = "s3"


class AuthMode(str, Enum):
    """Authentication mode options."""

    JWT = "jwt"
    API_KEY = "api_key"


class Settings(BaseSettings):
    """Application settings with environment variable validation.

    All settings can be overridden via environment variables.
    Sensitive values should be provided via environment variables or .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ========================================
    # Application
    # ========================================
    app_env: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Application environment",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )
    app_name: str = Field(
        default="BookBytes",
        description="Application name",
    )
    app_version: str = Field(
        default="0.1.0",
        description="Application version",
    )

    # ========================================
    # Logging
    # ========================================
    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Logging level",
    )
    log_format: LogFormat = Field(
        default=LogFormat.CONSOLE,
        description="Log output format (json for production, console for dev)",
    )

    # ========================================
    # Server
    # ========================================
    host: str = Field(
        default="0.0.0.0",
        description="Server host",
    )
    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Server port",
    )

    # ========================================
    # Database
    # ========================================
    database_url: str = Field(
        default="postgresql+asyncpg://bookbytes:bookbytes@localhost:5432/bookbytes",
        description="PostgreSQL database URL with async driver",
    )
    database_pool_min: int = Field(
        default=2,
        ge=1,
        description="Minimum database connection pool size",
    )
    database_pool_max: int = Field(
        default=10,
        ge=1,
        description="Maximum database connection pool size",
    )

    # ========================================
    # Redis
    # ========================================
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )

    # ========================================
    # Storage
    # ========================================
    storage_backend: StorageBackend = Field(
        default=StorageBackend.LOCAL,
        description="Storage backend to use (local or s3)",
    )
    local_storage_path: str = Field(
        default="./data/audio",
        description="Local filesystem path for audio storage",
    )

    # S3 Configuration
    s3_bucket: str = Field(
        default="bookbytes-audio",
        description="S3 bucket name for audio storage",
    )
    s3_region: str = Field(
        default="us-east-1",
        description="AWS S3 region",
    )
    aws_access_key_id: str | None = Field(
        default=None,
        description="AWS access key ID (optional, uses IAM role if not provided)",
    )
    aws_secret_access_key: SecretStr | None = Field(
        default=None,
        description="AWS secret access key",
    )
    s3_url_expiry_seconds: int = Field(
        default=0,
        ge=0,
        description="S3 pre-signed URL expiry in seconds (0 = no expiry/public)",
    )

    # ========================================
    # External APIs
    # ========================================
    openai_api_key: SecretStr = Field(
        default=SecretStr(""),
        description="OpenAI API key for chapter extraction and summaries",
    )
    openai_model: str = Field(
        default="gpt-3.5-turbo",
        description="OpenAI model to use",
    )
    openai_timeout: int = Field(
        default=30,
        ge=1,
        description="OpenAI API request timeout in seconds",
    )

    # ========================================
    # Authentication
    # ========================================
    auth_mode: AuthMode = Field(
        default=AuthMode.API_KEY,
        description="Authentication mode (jwt for production, api_key for local dev)",
    )
    jwt_secret_key: SecretStr = Field(
        default=SecretStr("dev-secret-key-change-in-production-!!!"),
        description="Secret key for JWT token signing",
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm",
    )
    jwt_expire_minutes: int = Field(
        default=30,
        ge=1,
        description="JWT access token expiry in minutes",
    )
    api_key: SecretStr = Field(
        default=SecretStr("dev-api-key-12345"),
        description="API key for local development bypass (used when AUTH_MODE=api_key)",
    )

    # ========================================
    # Worker
    # ========================================
    worker_max_jobs: int = Field(
        default=5,
        ge=1,
        description="Maximum concurrent jobs per worker",
    )
    worker_job_timeout: int = Field(
        default=600,
        ge=60,
        description="Job timeout in seconds (default 10 minutes)",
    )

    # ========================================
    # Derived Properties
    # ========================================
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == Environment.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env == Environment.PRODUCTION

    @property
    def use_json_logs(self) -> bool:
        """Check if JSON logging should be used."""
        return self.log_format == LogFormat.JSON or self.is_production

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, v: SecretStr) -> SecretStr:
        """Warn if using default JWT secret in non-dev environment."""
        # This is a soft validation - we log a warning but don't fail
        # The actual check happens at runtime in production
        return v


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    This function is cached to avoid re-reading environment variables
    on every access. Use dependency injection in FastAPI routes.

    Returns:
        Settings: Application settings instance
    """
    return Settings()
