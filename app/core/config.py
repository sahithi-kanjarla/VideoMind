from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


def find_env_file() -> Path:
    """Find the workspace .env regardless of the Uvicorn working directory."""
    for directory in Path(__file__).resolve().parents:
        candidate = directory / ".env"
        if candidate.is_file():
            return candidate
    return Path(".env")


class Settings(BaseSettings):
    app_name: str = "VideoMind API"
    environment: str = "development"

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    chroma_path: str = "chroma"
    groq_api_key: str | None = None
    sarvam_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=find_env_file(),
        extra="ignore",
    )


settings = Settings()
