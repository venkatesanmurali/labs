"""Analytics dashboard endpoint."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.holding import Holding
from app.models.option_trade import OptionTrade
from app.providers import get_provider
from app.schemas.analytics import (
    AnalyticsDashboard,
    DeltaBucket,
    MonthlyPremium,
    PnLSummary,
)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def _get_monthly_premiums(
    db: Session, owner: Optional[str] = None
) -> list[MonthlyPremium]:
    """Aggregate premiums by month from option_trades."""
    q = db.query(OptionTrade)
    if owner:
        q = q.filter(OptionTrade.owner == owner)
    trades = q.all()

    monthly: dict[str, dict] = defaultdict(
        lambda: {"total_premium": 0.0, "entry_count": 0}
    )
    for t in trades:
        month_key = t.trade_date.strftime("%Y-%m")
        if t.strategy_type == "STOCK":
            total = t.premium
        else:
            total = t.premium * t.contracts * 100
        monthly[month_key]["total_premium"] += total
        monthly[month_key]["entry_count"] += 1

    return [
        MonthlyPremium(
            month=month,
            total_premium=round(data["total_premium"], 2),
            entry_count=data["entry_count"],
        )
        for month, data in sorted(monthly.items())
    ]


def _get_delta_distribution(
    db: Session, owner: Optional[str] = None
) -> list[DeltaBucket]:
    """Compute delta distribution from current holdings with call options."""
    holdings = db.query(Holding).all()
    if owner:
        holdings = [h for h in holdings if h.owner == owner]

    # Only stock holdings can have covered calls; get their deltas via market data
    provider = get_provider()
    buckets: dict[str, int] = defaultdict(int)

    symbols = {h.symbol for h in holdings if h.holding_type == "stock"}
    for symbol in symbols:
        try:
            chain = provider.get_option_chain(symbol)
            for c in chain.contracts:
                if c.option_type != "call":
                    continue
                # Bucket by delta ranges
                d = abs(c.delta)
                if d < 0.10:
                    bucket = "0.00-0.10"
                elif d < 0.20:
                    bucket = "0.10-0.20"
                elif d < 0.30:
                    bucket = "0.20-0.30"
                elif d < 0.40:
                    bucket = "0.30-0.40"
                else:
                    bucket = "0.40+"
                buckets[bucket] += 1
        except Exception:
            continue

    return [
        DeltaBucket(bucket=b, count=c)
        for b, c in sorted(buckets.items())
    ]


def _get_pnl_summary(
    db: Session, owner: Optional[str] = None
) -> PnLSummary:
    """Compute P&L summary from trades."""
    q = db.query(OptionTrade)
    if owner:
        q = q.filter(OptionTrade.owner == owner)
    trades = q.all()

    total_premium = 0.0
    total_closed = 0.0
    open_count = 0

    for t in trades:
        if t.strategy_type == "STOCK":
            amt = t.premium
        else:
            amt = t.premium * t.contracts * 100
        if amt >= 0:
            total_premium += amt
        else:
            total_closed += amt

        # Count open positions (trade_type "fresh" without a corresponding close)
        if t.trade_type == "fresh":
            open_count += 1

    return PnLSummary(
        total_premium_collected=round(total_premium, 2),
        total_closed_cost=round(total_closed, 2),
        realized_pnl=round(total_premium + total_closed, 2),
        open_positions=open_count,
        unrealized_estimate=0.0,
    )


@router.get("/dashboard", response_model=AnalyticsDashboard)
def analytics_dashboard(
    owner: Optional[str] = Query(None, pattern=r"^(Venky|Bharg)$"),
    db: Session = Depends(get_db),
):
    """Full analytics dashboard: monthly premiums, delta distribution, P&L."""
    return AnalyticsDashboard(
        monthly_premiums=_get_monthly_premiums(db, owner),
        delta_distribution=_get_delta_distribution(db, owner),
        pnl=_get_pnl_summary(db, owner),
    )
