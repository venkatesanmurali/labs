"""
Abstract interface for market-data providers.

To add a new provider (Polygon, Tradier, TDA, etc.):
  1. Create a new file: providers/polygon_provider.py
  2. Subclass MarketDataProvider and implement all three methods.
  3. Register the provider key in providers/__init__.py:get_provider().
  4. Set MARKET_DATA_PROVIDER=polygon in .env
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Optional

from app.schemas.market_data import OptionChain, Quote, EarningsDate


class MarketDataProvider(ABC):
    """
    Abstract base class every market-data provider must implement.
    All methods are synchronous for simplicity; wrap with asyncio if needed.
    """

    @abstractmethod
    def get_quote(self, symbol: str) -> Quote:
        """Return the latest quote (price + timestamp) for *symbol*."""
        ...

    @abstractmethod
    def get_option_chain(
        self, symbol: str, as_of_date: Optional[date] = None
    ) -> OptionChain:
        """
        Return call-side option chain for *symbol*.
        Should include multiple expiries within a reasonable DTE range.
        *as_of_date* defaults to today.
        """
        ...

    @abstractmethod
    def get_earnings_calendar(self, symbol: str) -> EarningsDate:
        """Return the next scheduled earnings date for *symbol*."""
        ...
