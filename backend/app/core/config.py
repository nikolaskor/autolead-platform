"""
Application configuration using Pydantic Settings.
Loads environment variables from .env file.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str
    
    # Supabase (optional, for future use)
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    
    # Clerk Authentication
    CLERK_SECRET_KEY: str
    CLERK_PUBLISHABLE_KEY: str
    CLERK_JWKS_URL: Optional[str] = None
    CLERK_WEBHOOK_SECRET: str

    # Anthropic AI (for email classification and lead extraction)
    ANTHROPIC_API_KEY: Optional[str] = None

    # Facebook Lead Ads Integration
    FACEBOOK_APP_ID: Optional[str] = None
    FACEBOOK_APP_SECRET: Optional[str] = None
    FACEBOOK_VERIFY_TOKEN: Optional[str] = None
    FACEBOOK_PAGE_ACCESS_TOKEN: Optional[str] = None  # For testing with single page
    FACEBOOK_GRAPH_API_VERSION: str = "v21.0"

    # Application
    APP_NAME: str = "Norvalt API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_URL: str = "http://localhost:8000"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# Global settings instance
settings = Settings()

