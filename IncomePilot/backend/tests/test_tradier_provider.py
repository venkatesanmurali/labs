"""
Tests for the Tradier provider.

All HTTP calls are mocked so tests run offline.
"""

from datetime import date, datetime
from unittest.mock import patch, MagicMock

import pytest

from app.providers.tradier_provider import TradierProvider
from app.schemas.market_data import Quote, OptionChain, EarningsDate


@pytest.fixture
def provider():
    return TradierProvider(api_key="test-key", sandbox=True)


def _mock_response(json_data: dict, status_code: int = 200):
    resp = MagicMock()
    resp.json.return_value = json_data
    resp.status_code = status_code
    resp.raise_for_status = MagicMock()
    return resp


# ── Quote tests ───────────────────────────────────────────────────────────


@patch("app.providers.tradier_provider.httpx.Client")
def test_get_quote(mock_client_cls, provider):
    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.get.return_value = _mock_response(
        {"quotes": {"quote": {"symbol": "AAPL", "last": 185.0, "close": 184.5}}}
    )
    mock_client_cls.return_value = mock_client

    result = provider.get_quote("AAPL")

    assert isinstance(result, Quote)
    assert result.symbol == "AAPL"
    assert result.price == 185.0


@patch("app.providers.tradier_provider.httpx.Client")
def test_get_quote_uses_close_when_no_last(mock_client_cls, provider):
    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.get.return_value = _mock_response(
        {"quotes": {"quote": {"symbol": "AAPL", "last": None, "close": 184.5}}}
    )
    mock_client_cls.return_value = mock_client

    result = provider.get_quote("AAPL")
    assert result.price == 184.5


# ── Option chain tests ───────────────────────────────────────────────────


@patch("app.providers.tradier_provider.httpx.Client")
def test_get_option_chain_filters_calls_only(mock_client_cls, provider):
    today = date.today()
    exp = str(date.fromordinal(today.toordinal() + 14))

    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)

    # First call = quote, second = expirations, third = chain
    mock_client.get.side_effect = [
        _mock_response(
            {"quotes": {"quote": {"symbol": "AAPL", "last": 185.0}}}
        ),
        _mock_response({"expirations": {"date": [exp]}}),
        _mock_response(
            {
                "options": {
                    "option": [
                        {
                            "option_type": "call",
                            "strike": 190.0,
                            "bid": 2.0,
                            "ask": 2.5,
                            "last": 2.25,
                            "open_interest": 1000,
                            "volume": 200,
                            "greeks": {
                                "delta": 0.35,
                                "gamma": 0.02,
                                "theta": -0.08,
                                "mid_iv": 0.28,
                            },
                        },
                        {
                            "option_type": "put",
                            "strike": 190.0,
                            "bid": 5.0,
                            "ask": 5.5,
                            "last": 5.25,
                            "open_interest": 800,
                            "volume": 150,
                            "greeks": {
                                "delta": -0.65,
                                "gamma": 0.02,
                                "theta": -0.07,
                                "mid_iv": 0.29,
                            },
                        },
                    ]
                }
            }
        ),
    ]
    mock_client_cls.return_value = mock_client

    result = provider.get_option_chain("AAPL", as_of_date=today)

    assert isinstance(result, OptionChain)
    assert len(result.contracts) == 1  # only the call
    assert result.contracts[0].option_type == "call"
    assert result.contracts[0].delta == 0.35
    assert result.contracts[0].iv == 0.28


@patch("app.providers.tradier_provider.httpx.Client")
def test_get_option_chain_empty(mock_client_cls, provider):
    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)

    mock_client.get.side_effect = [
        _mock_response(
            {"quotes": {"quote": {"symbol": "XYZ", "last": 50.0}}}
        ),
        _mock_response({"expirations": {"date": []}}),
    ]
    mock_client_cls.return_value = mock_client

    result = provider.get_option_chain("XYZ")
    assert result.contracts == []


# ── Earnings tests ────────────────────────────────────────────────────────


@patch("app.providers.tradier_provider.httpx.Client")
def test_get_earnings_calendar(mock_client_cls, provider):
    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.get.return_value = _mock_response(
        {
            "results": [
                {
                    "tables": {
                        "corporate_calendars": {
                            "rows": [
                                {
                                    "event": "Earnings Release",
                                    "begin_date_time": "2027-01-28T00:00:00",
                                }
                            ]
                        }
                    }
                }
            ]
        }
    )
    mock_client_cls.return_value = mock_client

    result = provider.get_earnings_calendar("AAPL")
    assert isinstance(result, EarningsDate)
    assert result.next_earnings == date(2027, 1, 28)


@patch("app.providers.tradier_provider.httpx.Client")
def test_get_earnings_none(mock_client_cls, provider):
    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.get.return_value = _mock_response({"results": []})
    mock_client_cls.return_value = mock_client

    result = provider.get_earnings_calendar("QQQ")
    assert result.next_earnings is None


# ── Constructor tests ─────────────────────────────────────────────────────


def test_sandbox_url():
    p = TradierProvider(api_key="key", sandbox=True)
    assert "sandbox" in p.base_url


def test_prod_url():
    p = TradierProvider(api_key="key", sandbox=False)
    assert "sandbox" not in p.base_url
    assert "api.tradier.com" in p.base_url
