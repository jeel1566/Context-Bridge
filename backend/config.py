"""
Configuration Management for Context Bridge

Provides type-safe, validated configuration from environment variables.
Uses Pydantic settings for automatic validation and type coercion.
"""

import os
import logging
from typing import Optional
from functools import lru_cache

try:
    from pydantic_settings import BaseSettings
    from pydantic import Field, SecretStr
except ImportError:
    # Fallback for older pydantic
    from pydantic import BaseSettings, Field, SecretStr


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Azure Functions
    azure_web_jobs_storage: str = Field(
        default="UseDevelopmentStorage=true",
        alias="AzureWebJobsStorage"
    )
    functions_worker_runtime: str = Field(
        default="python",
        alias="FUNCTIONS_WORKER_RUNTIME"
    )
    
    # Google AI / ADK
    google_api_key: Optional[SecretStr] = Field(
        default=None,
        alias="GOOGLE_API_KEY"
    )
    gemini_api_key: Optional[SecretStr] = Field(
        default=None,
        alias="GEMINI_API_KEY"
    )
    
    # OpenRouter API
    openrouter_api_key: Optional[SecretStr] = Field(
        default=None,
        alias="OPENROUTER_API_KEY"
    )
    openrouter_model: str = Field(
        default="openai/gpt-oss-120b:free",
        alias="OPENROUTER_MODEL"
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        alias="OPENROUTER_BASE_URL"
    )
    
    # Cosmos DB
    cosmos_endpoint: Optional[str] = Field(
        default=None,
        alias="COSMOS_ENDPOINT"
    )
    cosmos_key: Optional[SecretStr] = Field(
        default=None,
        alias="COSMOS_KEY"
    )
    cosmos_connection: Optional[str] = Field(
        default=None,
        alias="COSMOS_CONNECTION"
    )
    cosmos_database: str = Field(
        default="contextbridge",
        alias="COSMOS_DATABASE"
    )
    
    # Security
    encryption_key: Optional[SecretStr] = Field(
        default=None,
        alias="ENCRYPTION_KEY"
    )
    jwt_secret_key: Optional[SecretStr] = Field(
        default=None,
        alias="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = Field(
        default="HS256",
        alias="JWT_ALGORITHM"
    )
    access_token_expire_minutes: int = Field(
        default=15,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    refresh_token_expire_days: int = Field(
        default=7,
        alias="REFRESH_TOKEN_EXPIRE_DAYS"
    )
    
    # Google OAuth
    google_client_id: Optional[str] = Field(
        default=None,
        alias="GOOGLE_CLIENT_ID"
    )
    
    # Environment
    environment: str = Field(
        default="development",
        alias="ENVIRONMENT"
    )
    debug: bool = Field(
        default=True,
        alias="DEBUG"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra env vars
    
    @property
    def effective_google_api_key(self) -> Optional[str]:
        """Get the effective Google API key (GOOGLE_API_KEY or GEMINI_API_KEY)."""
        if self.google_api_key:
            return self.google_api_key.get_secret_value()
        if self.gemini_api_key:
            return self.gemini_api_key.get_secret_value()
        return None
    
    @property
    def openrouter_configured(self) -> bool:
        """Check if OpenRouter is configured."""
        return bool(self.openrouter_api_key)
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment.lower() == "production"
    
    @property
    def cosmos_configured(self) -> bool:
        """Check if Cosmos DB is configured."""
        return bool(
            (self.cosmos_endpoint and self.cosmos_key) or
            self.cosmos_connection
        )
    
    @property
    def encryption_configured(self) -> bool:
        """Check if encryption is configured."""
        return bool(self.encryption_key)
    
    @property
    def jwt_configured(self) -> bool:
        """Check if JWT is configured."""
        return bool(self.jwt_secret_key)


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses lru_cache to ensure settings are only loaded once.
    In production, this provides a singleton-like behavior.
    """
    settings = Settings()
    
    # Log configuration status (without sensitive values)
    logger = logging.getLogger(__name__)
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Cosmos DB configured: {settings.cosmos_configured}")
    logger.info(f"Encryption configured: {settings.encryption_configured}")
    logger.info(f"JWT configured: {settings.jwt_configured}")
    logger.info(f"Google API key configured: {settings.effective_google_api_key is not None}")
    logger.info(f"OpenRouter configured: {settings.openrouter_configured}")
    if settings.openrouter_configured:
        logger.info(f"OpenRouter model: {settings.openrouter_model}")
    
    return settings


def validate_required_settings(settings: Settings) -> list[str]:
    """
    Validate that required settings are present.
    
    Returns:
        List of missing required settings
    """
    errors = []
    
    # For production, require all security settings
    if settings.is_production:
        if not settings.cosmos_configured:
            errors.append("Cosmos DB configuration required in production")
        if not settings.encryption_configured:
            errors.append("ENCRYPTION_KEY required in production")
        if not settings.jwt_configured:
            errors.append("JWT_SECRET_KEY required in production")
        if not settings.effective_google_api_key:
            errors.append("GOOGLE_API_KEY or GEMINI_API_KEY required")
    
    return errors


# Export commonly used items
__all__ = ['Settings', 'get_settings', 'validate_required_settings']
