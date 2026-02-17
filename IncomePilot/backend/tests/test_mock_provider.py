"""Tests for the mock market-data provider."""

from __future__ import annotations

from datetime import date

from app.providers.mock_provider import MockMarketDataProvider


def test_get_quote_known_ticker(mock_provider: MockMarketDataProvider):
    q = mock_provider.get_quote("AAPL")
    assert q.symbol == "AAPL"
    assert q.price == 228.0


def test_get_quote_unknown_ticker(mock_provider: MockMarketDataProvider):
    q = mock_provider.get_quote("XYZ")
    assert q.symbol == "XYZ"
    assert q.price == 100.0


def test_option_chain_has_contracts(mock_provider: MockMarketDataProvider):
    chain = mock_provider.get_option_chain("TSLA")
    assert chain.symbol == "TSLA"
    assert chain.spot == 340.0
    assert len(chain.contracts) > 0


def test_option_chain_contracts_are_calls(mock_provider: MockMarketDataProvider):
    chain = mock_provider.get_option_chain("META")
    for c in chain.contracts:
        assert c.option_type == "call"
        assert c.bid >= 0
        assert c.ask >= c.bid


def test_earnings_calendar(mock_provider: MockMarketDataProvider):
    e = mock_provider.get_earnings_calendar("TSLA")
    assert e.symbol == "TSLA"
    assert e.next_earnings == date(2025, 4, 22)


def test_earnings_etf_none(mock_provider: MockMarketDataProvider):
    e = mock_provider.get_earnings_calendar("QQQ")
    assert e.next_earnings is None
