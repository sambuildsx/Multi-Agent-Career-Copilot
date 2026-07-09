from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    PROJECT_NAME: str = "Recruiter Copilot"
    API_VERSION: str = "1.0.0"

    DATABASE_URL: str = "sqlite+aiosqlite:///careeros.db"
    DB_ECHO: bool = False

    SECRET_KEY: str = Field(..., description="JWT secret key")
    GOOGLE_API_KEY: str = Field(..., description="Google Gemini API Key")

    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    UPLOAD_DIRECTORY: str = "uploads"

    GEMINI_MODEL: str = "gemini-2.5-flash"

    ENVIRONMENT: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()