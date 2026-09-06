"""Application configuration settings."""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    PROJECT_NAME: str = "P24: Risk Rubric and Classifier"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    DATABASE_URL: str = "sqlite:///./p24_risk.db"
    DEBUG: bool = False

    # xAI Grok API Settings
    GROK_API_KEY: Optional[str] = None
    XAI_API_KEY: Optional[str] = None
    GROK_BASE_URL: str = "https://api.x.ai/v1"
    GROK_MODEL: str = "grok-2-latest"  # or grok-beta

    # Local Ollama AI Model Settings
    USE_OLLAMA: bool = True
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"  # or llama3, mistral, deepseek-r1, phi3

    # Optional Cloud API keys (fallback only if explicitly configured)
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # Default category score thresholds (Lower bounds for 1..4)
    CATEGORY_1_MAX: int = 6
    CATEGORY_2_MAX: int = 11
    CATEGORY_3_MAX: int = 16
    # 17+ is Category 4

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
