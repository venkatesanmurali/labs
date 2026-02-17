"""
Covered Call Recommendation Engine
===================================

Given a holding and market data, this engine:
1. Fetches the option chain via the configured MarketDataProvider.
2. Filters contracts by DTE, delta, open interest, volume, and earnings window.
3. Scores each candidate using a weighted composite:

    score = w_yield     * yield_score
          + w_delta_fit * delta_fit_score
          + w_liquidity * liquidity_score
          + w_distance  * distance_score
          + w_earnings  * earnings_safety_score

4. Returns the top-3 candidates with human-readable explanations.

All formulas are documented inline.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import List, Optional, Tuple

from app.providers.base import MarketDataProvider
from app.schemas.market_data import OptionContract
from app.schemas.recommendation import CandidateMetrics, RecommendationResponse


# ── Helpers ───────────────────────────────────────────────────────────────


def _clamp(val: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, val))


def _in_earnings_window(
    expiry: date,
    earnings_date: Optional[date],
    before_days: int,
    after_days: int,
) -> bool:
    """Return True if *expiry* falls within the blackout window around earnings."""
    if earnings_date is None:
        return False
    window_start = earnings_date - timedelta(days=before_days)
    window_end = earnings_date + timedelta(days=after_days)
    return window_start <= expiry <= window_end


# ── Scoring functions (each returns 0-1, higher = better) ────────────────


def score_yield(annualized_yield_pct: float, min_target: float) -> float:
    """
    Linearly scaled: 0 at min_target, 1 at 3× min_target, clamped [0, 1].
    formula: (annualized - min) / (2 * min)
    """
    if min_target <= 0:
        return 1.0
    return _clamp((annualized_yield_pct - min_target) / (2 * min_target))


def score_delta_fit(
    delta: float, target_min: float, target_max: float
) -> float:
    """
    1.0 when delta is in [target_min, target_max].
    Decays linearly outside the range; 0 when > 0.2 away.
    """
    if target_min <= delta <= target_max:
        return 1.0
    if delta < target_min:
        return _clamp(1 - (target_min - delta) / 0.2)
    return _clamp(1 - (delta - target_max) / 0.2)


def score_liquidity(open_interest: int, volume: int) -> float:
    """
    Combined OI + volume score.
    OI score: 0 at 0, 1 at 1000+
    Volume score: 0 at 0, 1 at 500+
    Final = 0.6 * OI_score + 0.4 * volume_score
    """
    oi_score = _clamp(open_interest / 1000)
    vol_score = _clamp(volume / 500)
    return 0.6 * oi_score + 0.4 * vol_score


def score_distance(moneyness_pct: float) -> float:
    """
    Prefer 2-8 % OTM.  Score peaks at 5 % OTM (moneyness_pct = 0.05).
    formula: 1 - |moneyness - 0.05| / 0.10  clamped [0, 1]
    """
    return _clamp(1 - abs(moneyness_pct - 0.05) / 0.10)


def score_earnings_safety(
    expiry: date,
    earnings_date: Optional[date],
    before_days: int,
    after_days: int,
) -> float:
    """1.0 if outside earnings window, 0.0 if inside."""
    if _in_earnings_window(expiry, earnings_date, before_days, after_days):
        return 0.0
    return 1.0


# ── Main engine ───────────────────────────────────────────────────────────


def recommend_covered_calls(
    symbol: str,
    provider: MarketDataProvider,
    *,
    # Strategy parameters (defaults match config.py)
    target_delta_min: float = 0.15,
    target_delta_max: float = 0.30,
    preferred_dte_min: int = 7,
    preferred_dte_max: int = 21,
    min_annualized_yield: float = 8.0,
    max_assignment_prob: float = 0.35,
    avoid_earnings_before: int = 7,
    avoid_earnings_after: int = 2,
    min_oi: int = 100,
    min_vol: int = 10,
    # Scoring weights
    w_yield: float = 0.35,
    w_delta_fit: float = 0.25,
    w_liquidity: float = 0.20,
    w_distance: float = 0.10,
    w_earnings_safety: float = 0.10,
    # Misc
    top_n: int = 3,
    dte_range: Tuple[int, int] = (1, 60),
) -> RecommendationResponse:
    """Run the full recommendation pipeline and return top-N candidates."""

    chain = provider.get_option_chain(symbol)
    spot = chain.spot
    earnings = provider.get_earnings_calendar(symbol)
    earnings_date = earnings.next_earnings

    # Earnings warning
    earnings_warning: Optional[str] = None
    if earnings_date:
        days_to_earnings = (earnings_date - date.today()).days
        if 0 < days_to_earnings <= 30:
            earnings_warning = (
                f"Earnings in {days_to_earnings} day(s) on {earnings_date}. "
                f"Contracts expiring within the blackout window are penalised."
            )

    # ── Step 1: Hard filters ─────────────────────────────────────────────
    candidates: List[OptionContract] = []
    for c in chain.contracts:
        if c.option_type != "call":
            continue
        if c.strike <= spot:
            continue  # only OTM calls (strike above current price)
        if not (dte_range[0] <= c.dte <= dte_range[1]):
            continue
        if abs(c.delta) > max_assignment_prob:
            continue
        if c.open_interest < min_oi and c.volume < min_vol:
            continue
        candidates.append(c)

    # Sort: nearest expiry first, then strikes ascending (just above spot)
    candidates.sort(key=lambda c: (c.expiry, c.strike))

    # ── Step 2: Compute metrics & score ──────────────────────────────────
    scored: List[CandidateMetrics] = []
    for c in candidates:
        # Use bid as the realistic fill price (most trades happen at bid)
        bid = c.bid
        premium_yield_pct = (bid / spot) * 100 if spot > 0 else 0
        annualized_yield_pct = premium_yield_pct * (365 / c.dte) if c.dte > 0 else 0
        moneyness_pct = (c.strike - spot) / spot if spot > 0 else 0

        # Sub-scores (each 0-1)
        s_yield = score_yield(annualized_yield_pct, min_annualized_yield)
        s_delta = score_delta_fit(abs(c.delta), target_delta_min, target_delta_max)
        s_liq = score_liquidity(c.open_interest, c.volume)
        s_dist = score_distance(moneyness_pct)
        s_earn = score_earnings_safety(
            c.expiry, earnings_date, avoid_earnings_before, avoid_earnings_after
        )

        composite = (
            w_yield * s_yield
            + w_delta_fit * s_delta
            + w_liquidity * s_liq
            + w_distance * s_dist
            + w_earnings_safety * s_earn
        )
        score_100 = round(composite * 100, 2)

        # ── Explanation text ─────────────────────────────────────────────
        why = (
            f"{c.strike} strike, {c.dte} DTE — "
            f"{moneyness_pct * 100:.1f}% OTM with delta {abs(c.delta):.2f}. "
            f"Annualised yield {annualized_yield_pct:.1f}%."
        )
        risk_note = (
            f"Assignment probability ≈ {abs(c.delta) * 100:.0f}% (delta proxy). "
            f"{'⚠ Inside earnings window.' if s_earn == 0 else 'Outside earnings window.'}"
        )
        income_note = (
            f"Premium ${bid:.2f}/share (${bid * 100:.0f}/contract). "
            f"Yield {premium_yield_pct:.2f}% per cycle, "
            f"{annualized_yield_pct:.1f}% annualised."
        )

        scored.append(
            CandidateMetrics(
                symbol=symbol,
                strike=c.strike,
                expiry=c.expiry,
                dte=c.dte,
                bid=c.bid,
                ask=c.ask,
                mid=mid,
                premium_yield_pct=round(premium_yield_pct, 4),
                annualized_yield_pct=round(annualized_yield_pct, 2),
                moneyness_pct=round(moneyness_pct, 4),
                prob_itm_proxy=round(abs(c.delta), 4),
                delta=c.delta,
                iv=c.iv,
                open_interest=c.open_interest,
                volume=c.volume,
                score=score_100,
                why=why,
                risk_note=risk_note,
                income_note=income_note,
            )
        )

    # ── Step 3: Sort & return top-N ──────────────────────────────────────
    scored.sort(key=lambda x: (x.expiry, x.strike))
    return RecommendationResponse(
        symbol=symbol,
        spot=spot,
        strategy_type="CC",
        earnings_warning=earnings_warning,
        candidates=scored[:top_n],
    )


# ── CSP Engine ────────────────────────────────────────────────────────────


def recommend_cash_secured_puts(
    symbol: str,
    provider: MarketDataProvider,
    *,
    target_delta_min: float = 0.15,
    target_delta_max: float = 0.30,
    preferred_dte_min: int = 7,
    preferred_dte_max: int = 21,
    min_annualized_yield: float = 8.0,
    max_assignment_prob: float = 0.35,
    avoid_earnings_before: int = 7,
    avoid_earnings_after: int = 2,
    min_oi: int = 100,
    min_vol: int = 10,
    w_yield: float = 0.35,
    w_delta_fit: float = 0.25,
    w_liquidity: float = 0.20,
    w_distance: float = 0.10,
    w_earnings_safety: float = 0.10,
    top_n: int = 3,
    dte_range: Tuple[int, int] = (1, 60),
) -> RecommendationResponse:
    """Run the CSP recommendation pipeline: sell OTM puts below current price."""

    chain = provider.get_option_chain(symbol)
    spot = chain.spot
    earnings = provider.get_earnings_calendar(symbol)
    earnings_date = earnings.next_earnings

    earnings_warning: Optional[str] = None
    if earnings_date:
        days_to_earnings = (earnings_date - date.today()).days
        if 0 < days_to_earnings <= 30:
            earnings_warning = (
                f"Earnings in {days_to_earnings} day(s) on {earnings_date}. "
                f"Contracts expiring within the blackout window are penalised."
            )

    # ── Step 1: Hard filters — puts only, strike < spot ────────────────
    candidates: List[OptionContract] = []
    for c in chain.contracts:
        if c.option_type != "put":
            continue
        if c.strike >= spot:
            continue  # only OTM puts (strike below current price)
        if not (dte_range[0] <= c.dte <= dte_range[1]):
            continue
        if abs(c.delta) > max_assignment_prob:
            continue
        if c.open_interest < min_oi and c.volume < min_vol:
            continue
        candidates.append(c)

    # Sort: nearest expiry first, then strikes descending (just below spot)
    candidates.sort(key=lambda c: (c.expiry, -c.strike))

    # ── Step 2: Compute metrics & score ────────────────────────────────
    scored: List[CandidateMetrics] = []
    for c in candidates:
        # Use bid as the realistic fill price (most trades happen at bid)
        bid = c.bid
        premium_yield_pct = (bid / spot) * 100 if spot > 0 else 0
        annualized_yield_pct = premium_yield_pct * (365 / c.dte) if c.dte > 0 else 0
        # For puts, moneyness = how far OTM below spot (positive = OTM)
        moneyness_pct = (spot - c.strike) / spot if spot > 0 else 0

        s_yield = score_yield(annualized_yield_pct, min_annualized_yield)
        s_delta = score_delta_fit(abs(c.delta), target_delta_min, target_delta_max)
        s_liq = score_liquidity(c.open_interest, c.volume)
        s_dist = score_distance(moneyness_pct)
        s_earn = score_earnings_safety(
            c.expiry, earnings_date, avoid_earnings_before, avoid_earnings_after
        )

        composite = (
            w_yield * s_yield
            + w_delta_fit * s_delta
            + w_liquidity * s_liq
            + w_distance * s_dist
            + w_earnings_safety * s_earn
        )
        score_100 = round(composite * 100, 2)

        why = (
            f"{c.strike} put strike, {c.dte} DTE — "
            f"{moneyness_pct * 100:.1f}% OTM with delta {abs(c.delta):.2f}. "
            f"Annualised yield {annualized_yield_pct:.1f}%."
        )
        risk_note = (
            f"Assignment probability ≈ {abs(c.delta) * 100:.0f}% (delta proxy). "
            f"If assigned, buy {symbol} at ${c.strike:.2f}. "
            f"{'⚠ Inside earnings window.' if s_earn == 0 else 'Outside earnings window.'}"
        )
        income_note = (
            f"Premium ${bid:.2f}/share (${bid * 100:.0f}/contract). "
            f"Yield {premium_yield_pct:.2f}% per cycle, "
            f"{annualized_yield_pct:.1f}% annualised."
        )

        scored.append(
            CandidateMetrics(
                symbol=symbol,
                strike=c.strike,
                expiry=c.expiry,
                dte=c.dte,
                bid=c.bid,
                ask=c.ask,
                mid=mid,
                premium_yield_pct=round(premium_yield_pct, 4),
                annualized_yield_pct=round(annualized_yield_pct, 2),
                moneyness_pct=round(moneyness_pct, 4),
                prob_itm_proxy=round(abs(c.delta), 4),
                delta=c.delta,
                iv=c.iv,
                open_interest=c.open_interest,
                volume=c.volume,
                score=score_100,
                why=why,
                risk_note=risk_note,
                income_note=income_note,
            )
        )

    scored.sort(key=lambda x: (x.expiry, -x.strike))
    return RecommendationResponse(
        symbol=symbol,
        spot=spot,
        strategy_type="CSP",
        earnings_warning=earnings_warning,
        candidates=scored[:top_n],
    )
