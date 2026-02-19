"""
Unit tests for the scoring functions in the recommendation engine.
Each scoring sub-function is tested for boundary conditions and expected behaviour.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.engines.recommendation_engine import (
    score_yield,
    score_delta_fit,
    score_liquidity,
    score_distance,
    score_earnings_safety,
    score_theta_efficiency,
    score_spread,
    _in_earnings_window,
)


# ── score_yield ──────────────────────────────────────────────────────────


class TestScoreYield:
    def test_at_minimum_is_zero(self):
        """Yield exactly at target → 0."""
        assert score_yield(8.0, 8.0) == 0.0

    def test_below_minimum_is_zero(self):
        assert score_yield(5.0, 8.0) == 0.0

    def test_at_triple_target_is_one(self):
        """3× target → 1.0."""
        assert score_yield(24.0, 8.0) == 1.0

    def test_mid_range(self):
        """16% yield with 8% target → (16 - 8) / 16 = 0.5."""
        assert score_yield(16.0, 8.0) == pytest.approx(0.5)

    def test_zero_target(self):
        """If min target is 0, any yield scores 1."""
        assert score_yield(1.0, 0.0) == 1.0


# ── score_delta_fit ──────────────────────────────────────────────────────


class TestScoreDeltaFit:
    def test_inside_range_is_one(self):
        assert score_delta_fit(0.20, 0.15, 0.30) == 1.0

    def test_at_boundary_is_one(self):
        assert score_delta_fit(0.15, 0.15, 0.30) == 1.0
        assert score_delta_fit(0.30, 0.15, 0.30) == 1.0

    def test_slightly_below(self):
        """0.10 is 0.05 below min (0.15); penalty = 0.05/0.2 = 0.25 → score 0.75."""
        assert score_delta_fit(0.10, 0.15, 0.30) == pytest.approx(0.75)

    def test_far_above(self):
        """0.50 is 0.20 above max → score 0."""
        assert score_delta_fit(0.50, 0.15, 0.30) == 0.0

    def test_very_low_delta(self):
        """Delta 0 → 0.15 / 0.2 = 0.75 penalty → score 0.25."""
        assert score_delta_fit(0.0, 0.15, 0.30) == pytest.approx(0.25)


# ── score_liquidity ──────────────────────────────────────────────────────


class TestScoreLiquidity:
    def test_high_liquidity(self):
        assert score_liquidity(2000, 1000) == pytest.approx(1.0)

    def test_zero_liquidity(self):
        assert score_liquidity(0, 0) == 0.0

    def test_partial(self):
        # OI 500/1000 → 0.5 * 0.6, Vol 250/500 → 0.5 * 0.4 = 0.3 + 0.2 = 0.5
        assert score_liquidity(500, 250) == pytest.approx(0.5)


# ── score_distance ───────────────────────────────────────────────────────


class TestScoreDistance:
    def test_ideal_otm(self):
        """5% OTM → peak score 1.0."""
        assert score_distance(0.05) == 1.0

    def test_atm(self):
        """0% OTM → 1 - 0.05/0.10 = 0.5."""
        assert score_distance(0.0) == pytest.approx(0.5)

    def test_deep_otm(self):
        """15% OTM → 1 - 0.10/0.10 = 0."""
        assert score_distance(0.15) == pytest.approx(0.0, abs=1e-12)

    def test_itm(self):
        """-5% (ITM) → 1 - 0.10/0.10 = 0."""
        assert score_distance(-0.05) == 0.0


# ── score_earnings_safety ────────────────────────────────────────────────


class TestScoreEarningsSafety:
    def test_no_earnings(self):
        assert score_earnings_safety(date(2025, 3, 21), None, 7, 2) == 1.0

    def test_inside_window(self):
        """Expiry 2 days before earnings → inside window → 0."""
        assert (
            score_earnings_safety(
                date(2025, 4, 20), date(2025, 4, 22), 7, 2
            )
            == 0.0
        )

    def test_outside_window(self):
        """Expiry well before earnings → safe → 1."""
        assert (
            score_earnings_safety(
                date(2025, 3, 1), date(2025, 4, 22), 7, 2
            )
            == 1.0
        )


# ── _in_earnings_window ─────────────────────────────────────────────────


class TestInEarningsWindow:
    def test_exact_earnings_date(self):
        assert _in_earnings_window(date(2025, 4, 22), date(2025, 4, 22), 7, 2)

    def test_day_after_earnings(self):
        assert _in_earnings_window(date(2025, 4, 23), date(2025, 4, 22), 7, 2)

    def test_day_before_window(self):
        """8 days before earnings with 7-day window → outside."""
        assert not _in_earnings_window(
            date(2025, 4, 14), date(2025, 4, 22), 7, 2
        )


# ── score_theta_efficiency ────────────────────────────────────────────


class TestScoreThetaEfficiency:
    def test_high_theta_relative_to_bid(self):
        """theta/bid ratio of 0.05+ → 1.0."""
        assert score_theta_efficiency(-0.10, 2.00) == 1.0

    def test_zero_theta(self):
        assert score_theta_efficiency(0.0, 2.00) == 0.0

    def test_zero_bid(self):
        assert score_theta_efficiency(-0.05, 0.0) == 0.0

    def test_mid_range(self):
        """theta/bid = 0.025 → 0.025/0.05 = 0.5."""
        assert score_theta_efficiency(-0.05, 2.00) == pytest.approx(0.5)


# ── score_spread ──────────────────────────────────────────────────────


class TestScoreSpread:
    def test_tight_spread(self):
        """Spread < 2% of mid → 1.0."""
        assert score_spread(10.00, 10.10) == pytest.approx(1.0)

    def test_wide_spread(self):
        """Spread > 20% of mid → 0.0."""
        assert score_spread(1.00, 1.50) == 0.0

    def test_mid_spread(self):
        """Spread = 11% of mid → between 0 and 1."""
        result = score_spread(1.00, 1.12)
        assert 0.0 < result < 1.0

    def test_zero_mid(self):
        assert score_spread(0.0, 0.0) == 0.0
