"""
Tests for the Yahoo Finance provider.

These tests mock the yfinance library so they run offline.
"""

from datetime import date, datetime
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from app.providers.yahoo_provider import YahooFinanceProvider
from app.schemas.market_data import Quote, OptionChain, EarningsDate


@pytest.fixture
def provider():
    return YahooFinanceProvider()


# ── Quote tests ───────────────────────────────────────────────────────────


@patch("app.providers.yahoo_provider.yf.Ticker")
def test_get_quote_returns_price(mock_ticker_cls, provider):
    mock_ticker = MagicMock()
    mock_fast_info = MagicMock()
    mock_fast_info.last_price = 185.50
    mock_ticker.fast_info = mock_fast_info
    mock_ticker_cls.return_value = mock_ticker

    result = provider.get_quote("AAPL")

    assert isinstance(result, Quote)
    assert result.symbol == "AAPL"
    assert result.price == 185.50


# ── Option chain tests ───────────────────────────────────────────────────


@patch("app.providers.yahoo_provider.yf.Ticker")
def test_get_option_chain_empty_expirations(mock_ticker_cls, provider):
    mock_ticker = MagicMock()
    mock_fast_info = MagicMock()
    mock_fast_info.last_price = 100.0
    mock_ticker.fast_info = mock_fast_info
    mock_ticker.options = []
    mock_ticker_cls.return_value = mock_ticker

    result = provider.get_option_chain("XYZ")

    assert isinstance(result, OptionChain)
    assert result.contracts == []
    assert result.spot == 100.0


@patch("app.providers.yahoo_provider.yf.Ticker")
def test_get_option_chain_filters_by_dte(mock_ticker_cls, provider):
    """Expirations beyond 60 DTE should be excluded."""
    import pandas as pd

    mock_ticker = MagicMock()
    mock_fast_info = MagicMock()
    mock_fast_info.last_price = 150.0
    mock_ticker.fast_info = mock_fast_info

    today = date.today()
    near_exp = str(date.fromordinal(today.toordinal() + 14))
    far_exp = str(date.fromordinal(today.toordinal() + 90))
    mock_ticker.options = [near_exp, far_exp]

    calls_df = pd.DataFrame(
        [
            {
                "strike": 155.0,
                "bid": 2.0,
                "ask": 2.5,
                "lastPrice": 2.25,
                "impliedVolatility": 0.30,
                "openInterest": 500,
                "volume": 100,
            }
        ]
    )
    chain_mock = MagicMock()
    chain_mock.calls = calls_df
    mock_ticker.option_chain.return_value = chain_mock
    mock_ticker_cls.return_value = mock_ticker

    result = provider.get_option_chain("TEST", as_of_date=today)

    # Only the near expiration should produce contracts
    assert len(result.contracts) == 1
    assert result.contracts[0].dte == 14


# ── Earnings tests ────────────────────────────────────────────────────────


@patch("app.providers.yahoo_provider.yf.Ticker")
def test_get_earnings_with_date(mock_ticker_cls, provider):
    mock_ticker = MagicMock()
    mock_ts = MagicMock()
    mock_ts.date.return_value = date(2026, 4, 25)
    mock_ticker.calendar = {"Earnings Date": [mock_ts]}
    mock_ticker_cls.return_value = mock_ticker

    result = provider.get_earnings_calendar("AAPL")

    assert isinstance(result, EarningsDate)
    assert result.next_earnings == date(2026, 4, 25)


@patch("app.providers.yahoo_provider.yf.Ticker")
def test_get_earnings_none(mock_ticker_cls, provider):
    mock_ticker = MagicMock()
    mock_ticker.calendar = {}
    mock_ticker_cls.return_value = mock_ticker

    result = provider.get_earnings_calendar("QQQ")

    assert result.next_earnings is None


# ── Greek approximation sanity checks ─────────────────────────────────────


def test_approx_delta_atm(provider):
    """ATM call delta should be near 0.5."""
    delta = provider._approx_delta(spot=100, strike=100, dte=30, iv=0.30)
    assert 0.45 <= delta <= 0.55


def test_approx_delta_deep_otm(provider):
    """Deep OTM call delta should be low."""
    delta = provider._approx_delta(spot=100, strike=150, dte=14, iv=0.25)
    assert delta < 0.10


def test_approx_delta_deep_itm(provider):
    """Deep ITM call delta should be high."""
    delta = provider._approx_delta(spot=100, strike=60, dte=14, iv=0.25)
    assert delta > 0.90


def test_approx_gamma_positive(provider):
    gamma = provider._approx_gamma(spot=100, strike=100, dte=30, iv=0.30)
    assert gamma > 0


def test_approx_theta_negative(provider):
    theta = provider._approx_theta(spot=100, strike=100, dte=30, iv=0.30, mid=5.0)
    assert theta < 0
