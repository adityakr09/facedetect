from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = (
        "postgresql+asyncpg://facedetect:facedetect_secret@db:5432/facedetect_db"
    )
    secret_key: str = "supersecretkey_change_in_production"
    log_level: str = "info"

    # Comma-separated list of allowed CORS origins
    cors_origins: str = "http://localhost"

    # Maximum dimension (px) a frame is downscaled to before detection
    # Smaller = faster detection, less accuracy
    detection_max_dim: int = 640

    # JPEG quality for annotated frames streamed to the frontend
    stream_jpeg_quality: int = 80


settings = Settings()
