"""
Provider registry.  Add new providers here.
"""

from __future__ import annotations

from functools import lru_cache

from app.config import get_settings
from app.providers.base import MarketDataProvider
from app.providers.mock_provider import MockMarketDataProvider


@lru_cache
def get_provider() -> MarketDataProvider:
    """
    Return the configured MarketDataProvider instance.
    Set MARKET_DATA_PROVIDER in .env to switch providers.
    """
    name = get_settings().market_data_provider.lower()
    if name == "mock":
        return MockMarketDataProvider()
    elif name == "yahoo":
        from app.providers.yahoo_provider import YahooFinanceProvider

        return YahooFinanceProvider()
    elif name == "tradier":
        from app.providers.tradier_provider import TradierProvider

        settings = get_settings()
        if not settings.tradier_api_key:
            raise ValueError(
                "TRADIER_API_KEY must be set in .env when using the Tradier provider"
            )
        return TradierProvider(
            api_key=settings.tradier_api_key,
            sandbox=settings.tradier_sandbox,
        )
    raise ValueError(f"Unknown market data provider: {name}")


__all__ = ["MarketDataProvider", "MockMarketDataProvider", "get_provider"]
