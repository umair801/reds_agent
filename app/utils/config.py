"""
Centralized settings loaded from .env file.
All secrets and config values live here.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Anthropic
    ANTHROPIC_API_KEY: str

    # GoHighLevel
    GHL_API_KEY: str
    GHL_LOCATION_ID: str
    GHL_BASE_URL: str = "https://services.leadconnectorhq.com"

    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str

    # App
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    PORT: int = 8080

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()