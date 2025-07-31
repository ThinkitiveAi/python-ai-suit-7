from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Application settings
    app_name: str = "Provider Registration API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database settings
    database_url: str = "postgresql://user:password@localhost/provider_registration"
    database_type: str = "postgresql"  # postgresql, mysql, mongodb

    # MongoDB settings (if using MongoDB)
    mongodb_url: Optional[str] = None
    mongodb_database: str = "provider_registration"

    # Security settings
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Password settings
    bcrypt_rounds: int = 12

    # Email settings
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: str = "noreply@provider-registration.com"

    # Redis settings (for rate limiting)
    redis_url: str = "redis://localhost:6379"

    # Rate limiting
    rate_limit_requests: int = 5
    rate_limit_window: int = 3600  # 1 hour in seconds

    # File upload settings
    upload_folder: str = "uploads"
    max_file_size: int = 10 * 1024 * 1024  # 10MB

    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/app.log"

    # CORS settings
    allowed_origins: list = ["http://localhost:3000", "http://localhost:8080"]

    class Config:
        env_file = ".env"
        case_sensitive = False


# Create settings instance
settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.upload_folder, exist_ok=True)
