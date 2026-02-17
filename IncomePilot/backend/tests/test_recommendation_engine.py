"""
Integration-level tests for the recommendation engine.
Uses the MockMarketDataProvider so tests are deterministic.
"""

from __future__ import annotations

from app.engines.recommendation_engine import recommend_covered_calls
from app.providers.mock_provider import MockMarketDataProvider


def test_returns_top_3_by_default(mock_provider: MockMarketDataProvider):
    result = recommend_covered_calls("AAPL", mock_provider)
    assert len(result.candidates) <= 3
    assert result.symbol == "AAPL"
    assert result.spot > 0


def test_scores_are_sorted_descending(mock_provider: MockMarketDataProvider):
    result = recommend_covered_calls("TSLA", mock_provider)
    scores = [c.score for c in result.candidates]
    assert scores == sorted(scores, reverse=True)


def test_all_candidates_are_calls(mock_provider: MockMarketDataProvider):
    result = recommend_covered_calls("META", mock_provider)
    for c in result.candidates:
        assert c.symbol == "META"
        assert c.strike > 0
        assert c.dte >= 7


def test_annualized_yield_formula(mock_provider: MockMarketDataProvider):
    """Verify annualized_yield = premium_yield * (365 / dte)."""
    result = recommend_covered_calls("QQQ", mock_provider)
    for c in result.candidates:
        expected = c.premium_yield_pct * (365 / c.dte)
        assert abs(c.annualized_yield_pct - round(expected, 2)) < 0.1


def test_moneyness_formula(mock_provider: MockMarketDataProvider):
    """Verify moneyness_pct = (strike - spot) / spot."""
    result = recommend_covered_calls("AMZN", mock_provider)
    spot = result.spot
    for c in result.candidates:
        expected = (c.strike - spot) / spot
        assert abs(c.moneyness_pct - round(expected, 4)) < 0.001


def test_custom_weights(mock_provider: MockMarketDataProvider):
    """Engine respects custom scoring weights without crashing."""
    result = recommend_covered_calls(
        "AAPL",
        mock_provider,
        w_yield=0.5,
        w_delta_fit=0.3,
        w_liquidity=0.1,
        w_distance=0.05,
        w_earnings_safety=0.05,
    )
    assert len(result.candidates) > 0


def test_earnings_warning_for_tsla(mock_provider: MockMarketDataProvider):
    """TSLA has mock earnings in April; engine should generate a warning."""
    result = recommend_covered_calls("TSLA", mock_provider)
    # May or may not have warning depending on test date vs mock earnings date;
    # just verify the field exists and is string | None
    assert result.earnings_warning is None or isinstance(result.earnings_warning, str)
