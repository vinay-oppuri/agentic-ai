# app/config.py
"""
Application Configuration
-------------------------
Loads environment variables and defines application settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Global application settings.
    """
    app_name: str = "Agentic AI Backend"
    environment: str = "dev"

    # Google GenAI Keys
    google_api_key: str
    
    # Task-Specific Keys (Optional - falls back to google_api_key if empty)
    google_key_planner: str
    google_key_competitor: str
    google_key_paper: str
    google_key_trend: str
    google_key_rag: str
    google_key_report: str

    gemini_model: str = "gemini-2.5-flash"

    # External APIs (Optional)
    tavily_api_key: str
    news_api_key: str

    # Database
    database_url: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()