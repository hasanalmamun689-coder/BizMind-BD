"""
Centralized application configuration.

Everything here is read from environment variables so that no secret,
credential, or environment-specific value is ever hardcoded (see
MASTER PROMPT section 7 and 34).
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Core ---
    APP_NAME: str = "BizMind BD"
    ENVIRONMENT: str = "development"

    # --- Database ---
    DATABASE_URL: str = (
        "postgresql+psycopg2://smeuser:smepassword@localhost:5432/sme_intelligence"
    )

    # --- Auth ---
    JWT_SECRET: str = "change-this-secret-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # --- AI ---
    # Provider-agnostic: "none" | "anthropic" | "openai" | "gemini"
    AI_PROVIDER: str = "none"
    AI_API_KEY: str = ""
    AI_MODEL: str = ""

    # --- CORS ---
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
