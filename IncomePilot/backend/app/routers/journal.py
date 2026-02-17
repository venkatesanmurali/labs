"""Journal CRUD + analytics router."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.journal import JournalEntry
from app.schemas.analytics import (
    AnalyticsDashboard,
    DeltaBucket,
    MonthlyPremium,
    PnLSummary,
)
from app.schemas.journal import JournalEntryCreate, JournalEntryOut, JournalEntryUpdate

router = APIRouter(prefix="/api/journal", tags=["journal"])


# ── CRUD ──────────────────────────────────────────────────────────────────


@router.get("", response_model=List[JournalEntryOut])
def list_entries(
    symbol: Optional[str] = Query(None),
    decision_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(JournalEntry)
    if symbol:
        q = q.filter(JournalEntry.symbol == symbol.upper())
    if decision_type:
        q = q.filter(JournalEntry.decision_type == decision_type)
    return q.order_by(JournalEntry.created_at.desc()).all()


@router.post("", response_model=JournalEntryOut, status_code=201)
def create_entry(payload: JournalEntryCreate, db: Session = Depends(get_db)):
    entry = JournalEntry(**payload.model_dump())
    entry.symbol = entry.symbol.upper()
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/{entry_id}", response_model=JournalEntryOut)
def get_entry(entry_id: int, db: Session = Depends(get_db)):
    e = db.get(JournalEntry, entry_id)
    if not e:
        raise HTTPException(404, "Journal entry not found")
    return e


@router.put("/{entry_id}", response_model=JournalEntryOut)
def update_entry(
    entry_id: int, payload: JournalEntryUpdate, db: Session = Depends(get_db)
):
    e = db.get(JournalEntry, entry_id)
    if not e:
        raise HTTPException(404, "Journal entry not found")
    for key, val in payload.model_dump(exclude_unset=True).items():
        setattr(e, key, val)
    db.commit()
    db.refresh(e)
    return e


@router.delete("/{entry_id}", status_code=204)
def delete_entry(entry_id: int, db: Session = Depends(get_db)):
    e = db.get(JournalEntry, entry_id)
    if not e:
        raise HTTPException(404, "Journal entry not found")
    db.delete(e)
    db.commit()


# ── Analytics ─────────────────────────────────────────────────────────────


@router.get("/analytics/dashboard", response_model=AnalyticsDashboard)
def analytics_dashboard(
    symbol: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(JournalEntry)
    if symbol:
        q = q.filter(JournalEntry.symbol == symbol.upper())
    entries: List[JournalEntry] = q.all()

    # Monthly premiums
    monthly: Dict[str, dict] = defaultdict(lambda: {"total": 0.0, "count": 0})
    for e in entries:
        if e.decision_type in ("sell", "roll") and e.premium:
            month_key = str(e.created_at)[:7]  # "YYYY-MM"
            monthly[month_key]["total"] += e.premium * e.contracts * 100
            monthly[month_key]["count"] += 1

    monthly_premiums = [
        MonthlyPremium(
            month=k, total_premium=round(v["total"], 2), entry_count=v["count"]
        )
        for k, v in sorted(monthly.items())
    ]

    # Delta distribution
    buckets: Dict[str, int] = defaultdict(int)
    for e in entries:
        if e.delta_at_entry is not None:
            d = abs(e.delta_at_entry)
            lo = int(d * 20) * 5  # buckets of 0.05
            hi = lo + 5
            buckets[f"0.{lo:02d}-0.{hi:02d}"] += 1

    delta_dist = [
        DeltaBucket(bucket=k, count=v) for k, v in sorted(buckets.items())
    ]

    # PnL
    total_premium = sum(
        (e.premium or 0) * e.contracts * 100
        for e in entries
        if e.decision_type in ("sell", "roll")
    )
    total_closed = sum(
        (e.closed_price or 0) * e.contracts * 100
        for e in entries
        if e.closed_price is not None
    )
    realized = total_premium - total_closed
    open_count = sum(
        1
        for e in entries
        if e.decision_type == "sell" and e.closed_price is None and not e.was_assigned
    )
    unrealized = sum(
        (e.premium or 0) * e.contracts * 100 * 0.5  # rough estimate: 50% captured
        for e in entries
        if e.decision_type == "sell" and e.closed_price is None and not e.was_assigned
    )

    pnl = PnLSummary(
        total_premium_collected=round(total_premium, 2),
        total_closed_cost=round(total_closed, 2),
        realized_pnl=round(realized, 2),
        open_positions=open_count,
        unrealized_estimate=round(unrealized, 2),
    )

    return AnalyticsDashboard(
        monthly_premiums=monthly_premiums,
        delta_distribution=delta_dist,
        pnl=pnl,
    )
