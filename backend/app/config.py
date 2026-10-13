"""Application configuration using Pydantic Settings v2.

Secret Key Generation:
Generate a secure random secret key using:
    python -c "import secrets; print(secrets.token_hex(32))"
or:
    openssl rand -hex 32
Set the generated key in your hosting environment configuration (e.g. Render dashboard)
as SECRET_KEY. Never commit secrets to version control or print them to stdout/logs.
"""

from functools import lru_cache
from typing import Any, List

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings for AI Business Architect."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application Environment
    app_env: str = Field(default="development", description="Environment: development, production, test")
    app_name: str = Field(default="AI Business Architect", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application semantic version")
    host: str = Field(default="0.0.0.0", description="Host to bind the server")
    port: int = Field(default=8000, description="Port to bind the server")

    # Security & Sessions
    secret_key: str = Field(
        default="development-insecure-secret-key-change-in-production-1234567890abcdef",
        description="Cryptographic secret key for session signing and CSRF tokens",
    )
    session_cookie_name: str = Field(default="aba_session", description="Session cookie name")
    session_max_age_seconds: int = Field(default=604800, description="Session lifespan in seconds (default 7 days)")
    session_https_only: bool = Field(default=False, description="Set Secure flag on session cookies (True in production)")
    session_same_site: str = Field(default="lax", description="SameSite cookie policy: lax, strict, none")

    # Database
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/ai_business_architect",
        description="SQLAlchemy database connection URL",
    )

    # AI Provider (Google Gemini)
    gemini_api_key: str = Field(default="", description="Google Gemini API key")
    gemini_model: str = Field(default="gemini-3-flash-preview", description="Gemini model identifier")
    ai_request_timeout_seconds: int = Field(default=60, description="Max timeout for AI requests in seconds")
    ai_max_retries: int = Field(default=3, description="Maximum retry count for transient AI errors")

    # Rate Limiting
    login_rate_limit_max_attempts: int = Field(default=5, description="Max login attempts allowed within window")
    login_rate_limit_window_seconds: int = Field(default=300, description="Rate limit window in seconds (5 minutes)")

    # CORS
    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:8000,http://127.0.0.1:8000",
        description="Comma-separated allowed CORS origins",
    )

    # Public Site URL & SEO
    public_site_url: str = Field(
        default="",
        description="Public canonical site URL for production deployment (e.g. https://your-service.onrender.com)",
    )

    # Logging
    log_level: str = Field(default="INFO", description="Log level: DEBUG, INFO, WARNING, ERROR")

    @field_validator("app_env")
    @classmethod
    def validate_app_env(cls, v: str) -> str:
        allowed = {"development", "production", "test"}
        val = v.strip().lower()
        if val not in allowed:
            raise ValueError(f"Invalid APP_ENV '{v}'. Allowed environments are: {', '.join(sorted(allowed))}")
        return val

    @field_validator("session_same_site")
    @classmethod
    def validate_session_same_site(cls, v: str) -> str:
        allowed = {"lax", "strict", "none"}
        val = v.strip().lower()
        if val not in allowed:
            raise ValueError(f"Invalid SESSION_SAME_SITE '{v}'. Allowed values are: {', '.join(sorted(allowed))}")
        return val

    @model_validator(mode="before")
    @classmethod
    def set_environment_defaults(cls, data: Any) -> Any:
        if isinstance(data, dict):
            env = str(data.get("app_env", "")).strip().lower()
            # In production, default session_https_only to True unless explicitly provided
            if env == "production" and "session_https_only" not in data:
                data["session_https_only"] = True
        return data

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.app_env.lower() == "production":
            key = self.secret_key.strip() if self.secret_key else ""
            if not key:
                raise ValueError(
                    "In production, SECRET_KEY must be a cryptographically secure key and cannot be empty. "
                    "Generate a secure key with: python -c \"import secrets; print(secrets.token_hex(32))\""
                )
            if len(key) < 32:
                raise ValueError(
                    f"In production, SECRET_KEY must be a cryptographically secure key of at least 32 characters "
                    f"(received {len(key)}). Generate a secure key with: python -c \"import secrets; print(secrets.token_hex(32))\""
                )
            lower_key = key.lower()
            weak_keywords = [
                "insecure",
                "development",
                "changeme",
                "default",
                "example",
                "placeholder",
                "12345678",
                "password",
            ]
            for kw in weak_keywords:
                if kw in lower_key:
                    raise ValueError(
                        f"In production, SECRET_KEY must be a cryptographically secure key and not contain weak or default patterns such as '{kw}'."
                    )

            if not self.gemini_api_key or not self.gemini_api_key.strip():
                raise ValueError("In production, GEMINI_API_KEY must be configured.")

            if not self.session_https_only:
                raise ValueError("In production, SESSION_HTTPS_ONLY must be set to True to ensure Secure cookies.")

            if self.session_same_site.lower() == "none" and not self.session_https_only:
                raise ValueError("SameSite=None cookies require SESSION_HTTPS_ONLY=True.")

        return self


    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def is_test(self) -> bool:
        return self.app_env.lower() == "test"

    @property
    def parsed_cors_origins(self) -> List[str]:
        if not self.cors_origins:
            return []
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def normalized_database_url(self) -> str:
        """Ensure postgresql connection URLs use the psycopg (v3) driver dialect in SQLAlchemy."""
        url = self.database_url.strip()
        if url.startswith("postgres://"):
            return "postgresql+psycopg://" + url[len("postgres://"):]
        if url.startswith("postgresql://") and not url.startswith("postgresql+psycopg://"):
            return "postgresql+psycopg://" + url[len("postgresql://"):]
        return url


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Singleton getter for application settings."""
    return Settings()
