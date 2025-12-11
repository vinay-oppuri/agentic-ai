# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Agentic AI Backend"
    environment: str = "dev"

    # Comma-separated list of Google GenAI API keys (preferred) OR single fallback key
    google_keys: str
    google_api_key: str

    gemini_model: str = "gemini-2.5-flash"

    # Optional external APIs
    tavily_api_key: str
    news_api_key: str

    database_url: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()