"""
Roll Decision Engine
====================

Given an existing short call position, decide whether to:
  1. Hold
  2. Close
  3. Roll out  (same strike, later expiry)
  4. Roll up & out  (higher strike, later expiry)
  5. Accept assignment

Decision rules:
- Compute intrinsic = max(spot - strike, 0)
- Compute extrinsic = option_mid - intrinsic
- If DTE <= 2 AND deep ITM (intrinsic > 2 * extrinsic) AND no credit roll
  available → accept_assignment
- If DTE <= 2 AND deep ITM AND credit roll available → roll_out or roll_up_and_out
- If ITM AND gamma high (DTE < 5) → prefer roll_out to reduce gamma risk
- If OTM AND extrinsic > 50 % of mid → hold (time decay still working)
- Otherwise → evaluate rolls; if net credit available, roll.

The engine also returns a "what-if" table of up to 3 roll alternatives.
"""

from __future__ import annotations

from datetime import date
from typing import List

from app.providers.base import MarketDataProvider
from app.schemas.roll import RollAlternative, RollDecision, RollRequest


def evaluate_roll(
    req: RollRequest,
    provider: MarketDataProvider,
    *,
    target_delta_min: float = 0.15,
    target_delta_max: float = 0.30,
    roll_max_debit: float = 0.50,
    roll_min_dte: int = 7,
    roll_max_dte: int = 45,
) -> RollDecision:
    """
    Run the roll decision pipeline.

    Parameters
    ----------
    req : RollRequest
        Current short call details.
    provider : MarketDataProvider
        Data source for option chains.
    target_delta_min / target_delta_max : float
        Acceptable delta range for roll targets.
    roll_max_debit : float
        Maximum net debit ($) the user will accept on a roll.
    roll_min_dte / roll_max_dte : int
        DTE search window for roll candidates.
    """
    spot = req.current_spot
    strike = req.strike
    option_mid = req.current_option_mid
    dte = req.days_to_expiry

    # ── Intrinsic / extrinsic decomposition ──────────────────────────────
    intrinsic = max(spot - strike, 0.0)
    extrinsic = max(option_mid - intrinsic, 0.0)

    is_itm = spot > strike
    deep_itm = intrinsic > 2 * extrinsic if extrinsic > 0 else (intrinsic > 0)
    high_gamma_zone = dte <= 5 and is_itm

    # ── Fetch roll candidates from the chain ─────────────────────────────
    chain = provider.get_option_chain(req.symbol)
    roll_candidates: List[RollAlternative] = []
    for c in chain.contracts:
        if c.option_type != "call":
            continue
        if not (roll_min_dte <= c.dte <= roll_max_dte):
            continue
        # Must be a later expiry than current
        if c.expiry <= req.expiry:
            continue
        # Keep delta in acceptable range
        if not (target_delta_min <= abs(c.delta) <= target_delta_max + 0.10):
            continue
        # Must be same or higher strike (no rolling down for covered calls)
        if c.strike < strike:
            continue

        # Net credit = what we collect (selling new at bid) - what we pay (buying back old)
        # Positive = credit; negative = debit
        net_credit = round(c.bid - option_mid, 2)

        # Skip if debit exceeds threshold
        if net_credit < -roll_max_debit:
            continue

        new_moneyness = (c.strike - spot) / spot if spot > 0 else 0

        explanation = (
            f"Roll to {c.strike} strike, {c.expiry} ({c.dte} DTE). "
            f"Net {'credit' if net_credit >= 0 else 'debit'} ${abs(net_credit):.2f}. "
            f"New delta {abs(c.delta):.2f}, {new_moneyness * 100:.1f}% OTM."
        )

        roll_candidates.append(
            RollAlternative(
                strike=c.strike,
                expiry=c.expiry,
                dte=c.dte,
                bid=c.bid,
                ask=c.ask,
                mid=c.mid,
                delta=c.delta,
                net_credit=net_credit,
                new_moneyness_pct=round(new_moneyness, 4),
                explanation=explanation,
            )
        )

    # Sort: prefer credit rolls, then by strike (higher = better for covered calls)
    roll_candidates.sort(key=lambda x: (x.net_credit >= 0, x.net_credit, x.strike), reverse=True)
    top_alternatives = roll_candidates[:3]

    # ── Decision logic ───────────────────────────────────────────────────
    has_credit_roll = any(a.net_credit >= 0 for a in top_alternatives)
    best_roll = top_alternatives[0] if top_alternatives else None

    if dte <= 2 and deep_itm:
        if has_credit_roll and best_roll:
            if best_roll.strike > strike:
                action = "roll_up_and_out"
                explanation = (
                    f"Position is deep ITM with only ${extrinsic:.2f} extrinsic remaining "
                    f"and expiry imminent. A credit roll to {best_roll.strike} strike "
                    f"({best_roll.expiry}) collects ${best_roll.net_credit:.2f} net credit "
                    f"while improving the strike."
                )
            else:
                action = "roll_out"
                explanation = (
                    f"Position is deep ITM with ${extrinsic:.2f} extrinsic and expiry imminent. "
                    f"Rolling out to {best_roll.expiry} at same strike for "
                    f"${best_roll.net_credit:.2f} net credit to buy more time."
                )
        else:
            action = "accept_assignment"
            explanation = (
                f"Position is deep ITM (intrinsic ${intrinsic:.2f}, extrinsic ${extrinsic:.2f}) "
                f"with expiry imminent and no attractive roll available. "
                f"Accept assignment and re-evaluate selling a new call."
            )
    elif high_gamma_zone:
        if has_credit_roll and best_roll:
            action = "roll_out"
            explanation = (
                f"High gamma risk zone (DTE={dte}, ITM). "
                f"Rolling out to {best_roll.expiry} reduces pin risk. "
                f"Net credit ${best_roll.net_credit:.2f}."
            )
        else:
            action = "close"
            explanation = (
                f"High gamma risk zone (DTE={dte}, ITM) with no good roll candidates. "
                f"Close the position to eliminate assignment risk. "
                f"Cost to close: ${option_mid:.2f}."
            )
    elif not is_itm and extrinsic > 0.5 * option_mid and dte > 5:
        action = "hold"
        explanation = (
            f"Position is OTM with ${extrinsic:.2f} extrinsic (time value still decaying). "
            f"{dte} DTE remaining. Theta is working in your favour — hold."
        )
    elif has_credit_roll and best_roll:
        if best_roll.strike > strike:
            action = "roll_up_and_out"
            explanation = (
                f"Rolling up to {best_roll.strike} strike and out to {best_roll.expiry} "
                f"for ${best_roll.net_credit:.2f} net credit. "
                f"Improves strike while collecting additional premium."
            )
        else:
            action = "roll_out"
            explanation = (
                f"Rolling out to {best_roll.expiry} at {best_roll.strike} strike "
                f"for ${best_roll.net_credit:.2f} net credit."
            )
    else:
        action = "hold"
        explanation = (
            f"No compelling action. Extrinsic ${extrinsic:.2f}, DTE {dte}. "
            f"Continue to hold and monitor."
        )

    return RollDecision(
        action=action,
        explanation=explanation,
        current_extrinsic=round(extrinsic, 2),
        current_intrinsic=round(intrinsic, 2),
        alternatives=top_alternatives,
    )
