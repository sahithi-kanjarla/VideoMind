from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "VideoMind API"
    environment: str = "development"

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    chroma_path: str = "chroma"
    groq_api_key: str | None = None
    sarvam_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
