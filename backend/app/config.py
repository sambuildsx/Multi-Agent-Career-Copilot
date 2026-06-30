from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "CareerOS"
    DATABASE_URL: str = "sqlite+aiosqlite:///careeros.db"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "careeros-super-secret-key-change-in-production"
    GOOGLE_API_KEY: str = "placeholder"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
