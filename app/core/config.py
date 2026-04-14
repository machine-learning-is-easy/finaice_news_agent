from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/finance_news"
    database_sync_url: str = "postgresql://postgres:password@localhost:5432/finance_news"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # LLM
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # Embedding
    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536

    # Reasoning model
    reasoning_model: str = "claude-sonnet-4-6"
    reasoning_max_tokens: int = 2048

    # News ingestion
    rss_feeds: str = ""
    sec_user_agent: str = "FinanceNewsAgent contact@example.com"
    ingestion_interval_seconds: int = 300

    # Alert thresholds
    alert_impact_threshold: float = 0.7
    alert_novelty_threshold: float = 0.6

    # Email / SMTP
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""

    @property
    def rss_feed_list(self) -> list[str]:
        return [f.strip() for f in self.rss_feeds.split(",") if f.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
