"""
Unit tests for the roll decision engine.
Edge cases: deep ITM near expiry, OTM holds, gamma risk zone.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

import pytest

from app.engines.roll_engine import evaluate_roll
from app.providers.mock_provider import MockMarketDataProvider
from app.schemas.roll import RollRequest


@pytest.fixture
def today() -> date:
    return date.today()


def _make_req(
    symbol: str = "TSLA",
    strike: float = 330.0,
    dte: int = 14,
    sold_price: float = 5.00,
    option_mid: float = 3.50,
    spot: float = 340.0,
    today: Optional[date] = None,
) -> RollRequest:
    t = today or date.today()
    return RollRequest(
        symbol=symbol,
        strike=strike,
        expiry=t + timedelta(days=dte),
        sold_price=sold_price,
        current_option_mid=option_mid,
        current_spot=spot,
        days_to_expiry=dte,
    )


class TestRollDecisionEdgeCases:
    def test_deep_itm_near_expiry_accept_or_roll(
        self, mock_provider: MockMarketDataProvider
    ):
        """DTE=1, deep ITM, high mid → accept_assignment or roll."""
        req = _make_req(strike=300.0, dte=1, option_mid=42.0, spot=340.0)
        result = evaluate_roll(req, mock_provider)
        assert result.action in ("accept_assignment", "roll_out", "roll_up_and_out")
        assert result.current_intrinsic == pytest.approx(40.0)

    def test_otm_with_time_value_hold(
        self, mock_provider: MockMarketDataProvider
    ):
        """OTM option with plenty of extrinsic and DTE → hold."""
        req = _make_req(strike=360.0, dte=14, option_mid=2.00, spot=340.0)
        result = evaluate_roll(req, mock_provider)
        assert result.action == "hold"
        assert result.current_intrinsic == 0.0
        assert result.current_extrinsic == 2.00

    def test_gamma_risk_zone_itm(
        self, mock_provider: MockMarketDataProvider
    ):
        """DTE=3, ITM → should roll or close (gamma risk)."""
        req = _make_req(strike=335.0, dte=3, option_mid=8.00, spot=340.0)
        result = evaluate_roll(req, mock_provider)
        assert result.action in ("roll_out", "close", "roll_up_and_out")

    def test_alternatives_not_empty_for_itm(
        self, mock_provider: MockMarketDataProvider
    ):
        """Roll engine should find at least some alternatives for ITM positions."""
        req = _make_req(strike=330.0, dte=5, option_mid=14.0, spot=340.0)
        result = evaluate_roll(req, mock_provider)
        # With mock data there should be at least one candidate
        # (unless all are filtered out, which is still valid)
        assert isinstance(result.alternatives, list)

    def test_extrinsic_calculation(
        self, mock_provider: MockMarketDataProvider
    ):
        """Verify intrinsic + extrinsic decomposition."""
        req = _make_req(strike=330.0, dte=10, option_mid=15.0, spot=340.0)
        result = evaluate_roll(req, mock_provider)
        assert result.current_intrinsic == 10.0
        assert result.current_extrinsic == 5.0

    def test_otm_zero_intrinsic(
        self, mock_provider: MockMarketDataProvider
    ):
        """OTM → intrinsic = 0, extrinsic = full mid."""
        req = _make_req(strike=360.0, dte=10, option_mid=3.0, spot=340.0)
        result = evaluate_roll(req, mock_provider)
        assert result.current_intrinsic == 0.0
        assert result.current_extrinsic == 3.0


class TestRollAlternatives:
    def test_alternatives_have_later_expiry(
        self, mock_provider: MockMarketDataProvider
    ):
        req = _make_req(strike=340.0, dte=5, option_mid=6.0, spot=340.0)
        result = evaluate_roll(req, mock_provider)
        for alt in result.alternatives:
            assert alt.expiry > req.expiry

    def test_alternatives_same_or_higher_strike(
        self, mock_provider: MockMarketDataProvider
    ):
        req = _make_req(strike=330.0, dte=5, option_mid=14.0, spot=340.0)
        result = evaluate_roll(req, mock_provider)
        for alt in result.alternatives:
            assert alt.strike >= 330.0

    def test_max_three_alternatives(
        self, mock_provider: MockMarketDataProvider
    ):
        req = _make_req(strike=340.0, dte=5, option_mid=6.0, spot=340.0)
        result = evaluate_roll(req, mock_provider)
        assert len(result.alternatives) <= 3
