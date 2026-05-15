from __future__ import annotations

from app.config import settings
from app.providers.base import MarketDataProvider


def build_provider() -> MarketDataProvider:
    """
    Returns the appropriate provider based on environment config:
      POLYGON_API_KEY set  + USE_REDIS=true  → RedisCache(PolygonProvider)
      POLYGON_API_KEY set  + USE_REDIS=false → PolygonProvider
      No key               + USE_REDIS=true  → RedisCache(YFinanceProvider)
      No key               + USE_REDIS=false → YFinanceProvider  (default / dev)
    """
    from app.providers.yfinance_provider import YFinanceProvider
    from app.providers.polygon_provider import PolygonProvider
    from app.providers.redis_cache import RedisCache

    if settings.polygon_api_key:
        base: MarketDataProvider = PolygonProvider(api_key=settings.polygon_api_key)
    else:
        base = YFinanceProvider()

    if settings.use_redis:
        return RedisCache(inner=base, redis_url=settings.redis_url)
    return base
