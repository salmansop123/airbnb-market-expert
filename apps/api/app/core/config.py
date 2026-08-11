from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "StayPrice AI"
    APP_ENV: str = "development"
    APP_VERSION: str = "1.1.0"
    API_V1_PREFIX: str = "/v1"
    SECRET_KEY: str = "change-me-in-production-use-long-random-string"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14
    ALGORITHM: str = "HS256"

    DATABASE_URL: str = "postgresql+asyncpg://stayprice:stayprice@localhost:5436/stayprice"
    DATABASE_URL_SYNC: str = "postgresql://stayprice:stayprice@localhost:5436/stayprice"

    REDIS_URL: str = "redis://localhost:6382/0"
    CELERY_BROKER_URL: str = "redis://localhost:6382/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6382/1"
    CELERY_ALWAYS_EAGER: bool = False

    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_DEFAULT_MODEL: str = "openai/gpt-4o-mini"
    OPENROUTER_VISION_MODEL: str = "openai/gpt-4o-mini"
    OPENROUTER_REPORT_MODEL: str = "openai/gpt-4o-mini"

    AWS_ACCESS_KEY_ID: str = "minioadmin"
    AWS_SECRET_ACCESS_KEY: str = "minioadmin"
    AWS_REGION: str = "us-east-1"
    S3_BUCKET: str = "stayprice"
    S3_ENDPOINT_URL: str | None = "http://localhost:9000"
    S3_PUBLIC_BASE_URL: str = "http://localhost:9000/stayprice"

    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRO_PRICE_ID: str = ""
    STRIPE_BUSINESS_PRICE_ID: str = ""
    FRONTEND_URL: str = "http://localhost:3000"

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "StayPrice AI <noreply@stayprice.ai>"
    RESEND_API_KEY: str = ""

    SENTRY_DSN: str = ""
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = True

    RATE_LIMIT_PER_MINUTE: int = 60
    AUTH_RATE_LIMIT_PER_MINUTE: int = 20
    ANALYZE_RATE_LIMIT_PER_HOUR: int = 30

    FREE_PROPERTY_LIMIT: int = 5
    FREE_ANALYSES_PER_MONTH: int = 10
    FREE_VISION_PHOTOS: int = 3
    FREE_CHAT_PER_DAY: int = 20
    PRO_ANALYSES_PER_MONTH: int = 500
    BUSINESS_ANALYSES_PER_MONTH: int = 5000

    MODEL_ARTIFACTS_DIR: str = "app/ml/artifacts"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() in {"production", "prod"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
