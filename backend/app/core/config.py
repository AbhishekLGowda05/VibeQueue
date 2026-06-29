"""
app/core/config.py

Central configuration — all settings read from environment variables.
Uses pydantic-settings so every value is validated at startup.
If a required value is missing, the app refuses to start (fail-fast).
"""

from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── App ──────────────────────────────────────────────────────────
    APP_NAME: str = "VibeQueue"
    APP_ENV: str = "development"
    APP_DEBUG: bool = False
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_WORKERS: int = 1
    SECRET_KEY: str

    # ── Database ─────────────────────────────────────────────────────
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # ── Redis ────────────────────────────────────────────────────────
    REDIS_URL: str
    REDIS_QUEUE_DB: int = 1
    REDIS_CELERY_DB: int = 2
    REDIS_TTL_QUEUE: int = 7200

    # ── JWT ──────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ── Celery ───────────────────────────────────────────────────────
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # ── Razorpay ─────────────────────────────────────────────────────
    RAZORPAY_KEY_ID: str
    RAZORPAY_KEY_SECRET: str
    RAZORPAY_WEBHOOK_SECRET: str

    # ── YouTube ──────────────────────────────────────────────────────
    YOUTUBE_API_KEY: str
    YOUTUBE_QUOTA_LIMIT: int = 9500

    # ── WhatsApp ─────────────────────────────────────────────────────
    WHATSAPP_API_TOKEN: str
    WHATSAPP_PHONE_NUMBER_ID: str
    WHATSAPP_BUSINESS_ACCOUNT_ID: str

    # ── Cloudflare R2 ────────────────────────────────────────────────
    R2_ACCOUNT_ID: str
    R2_ACCESS_KEY_ID: str
    R2_SECRET_ACCESS_KEY: str
    R2_BUCKET_NAME: str = "vibequeue-assets"
    R2_PUBLIC_URL: str

    # ── Sentry ───────────────────────────────────────────────────────
    SENTRY_DSN: str = ""
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1

    # ── CORS ─────────────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:5173"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str) -> List[str]:
        return [origin.strip() for origin in v.split(",")]

    # ── Business Logic ───────────────────────────────────────────────
    DEFAULT_QUEUE_SIZE_LIMIT: int = 8
    DEFAULT_SPEND_CAP_PAISE: int = 15000      # ₹150 in paise
    DEFAULT_REQUEST_COOLDOWN_SECONDS: int = 180
    TABLE_CODE_EXPIRY_SECONDS: int = 5400     # 90 minutes
    QUEUE_SONG_EXPIRY_SECONDS: int = 5400
    PLAYBACK_WATCHDOG_SECONDS: int = 60
    FALLBACK_TRIGGER_SECONDS: int = 30

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"


@lru_cache()
def get_settings() -> Settings:
    """
    Cached singleton — settings are read once at startup.
    Use dependency injection: Depends(get_settings) in routes.
    """
    return Settings()


# Module-level shorthand for non-DI contexts (services, workers)
settings = get_settings()
