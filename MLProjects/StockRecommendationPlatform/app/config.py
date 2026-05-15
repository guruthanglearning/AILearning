from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    redis_url: str = "redis://localhost:6379/0"
    use_redis: bool = False
    stock_prediction_api_url: str | None = None
    quote_stale_seconds: int = 120
    agent_timeout_seconds: float = 45.0

    # Phase 0 — Postgres
    database_url: str = "postgresql+asyncpg://rec:rec@localhost:5433/recommendation"

    # Phase 0b — Polygon (absent → yfinance fallback)
    polygon_api_key: str | None = None


settings = Settings()
