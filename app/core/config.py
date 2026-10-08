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

    # Database configuration
    database_url: str | None = None

    # Supabase configuration
    supabase_url: str | None = None
    supabase_key: str | None = None

    # Gemini configuration
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"

    # Local services
    chroma_path: str = "chroma"
    groq_api_key: str | None = None
    sarvam_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=find_env_file(),
        extra="ignore",
    )

    @property
    def db_url(self) -> str:
        """Get the database URL, preferring DATABASE_URL over supabase_url."""
        if self.database_url and "obmbpxsgecnkzzomcqlk" not in self.database_url:
            return self.database_url
        # Fallback to SQLite for local development if Supabase is unreachable
        return "sqlite:///./videomind.db"


settings = Settings()
