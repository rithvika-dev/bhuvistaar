from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str

    UPLOAD_DIR: str = "uploads"
    PROCESSED_DIR: str = "processed"
    EXPORT_DIR: str = "exports"

    # Redis/Celery
    REDIS_URL: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"


settings = Settings()