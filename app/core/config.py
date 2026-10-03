from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "VideoMind API"
    environment: str = "development"

    gemini_api_key: str | None = None
    groq_api_key: str | None = None
    sarvam_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()