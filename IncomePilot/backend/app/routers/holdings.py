"""Holdings CRUD + CSV import router."""

from __future__ import annotations

import csv
import io
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.holding import Holding
from app.providers import get_provider
from app.schemas.holding import (
    CSVImportResult,
    HoldingCreate,
    HoldingOut,
    HoldingUpdate,
)
from app.schemas.analytics import NetWorthHolding, NetWorthSummary

router = APIRouter(prefix="/api/holdings", tags=["holdings"])


@router.get("", response_model=List[HoldingOut])
def list_holdings(
    owner: Optional[str] = Query(None, pattern=r"^(Venky|Bharg)$"),
    db: Session = Depends(get_db),
):
    q = db.query(Holding)
    if owner:
        q = q.filter(Holding.owner == owner)
    return q.order_by(Holding.symbol).all()


@router.post("", response_model=HoldingOut, status_code=201)
def create_holding(payload: HoldingCreate, db: Session = Depends(get_db)):
    h = Holding(**payload.model_dump())
    db.add(h)
    db.commit()
    db.refresh(h)
    return h


@router.get("/net-worth", response_model=NetWorthSummary)
def net_worth(db: Session = Depends(get_db)):
    holdings = db.query(Holding).all()
    if not holdings:
        return NetWorthSummary(total_net_worth=0, holdings=[], by_owner={})

    provider = get_provider()
    symbols = list({h.symbol for h in holdings})
    prices = {}
    for sym in symbols:
        try:
            q = provider.get_quote(sym)
            prices[sym] = q.price
        except Exception:
            prices[sym] = 0.0

    result_holdings = []
    total = 0.0
    by_owner: dict[str, float] = {}

    for h in holdings:
        price = prices.get(h.symbol, 0.0)
        if h.holding_type == "leaps" and h.strike is not None:
            if h.option_type == "call":
                intrinsic = max(0.0, price - h.strike)
            else:
                intrinsic = max(0.0, h.strike - price)
            market_value = intrinsic * 100 * h.shares
        else:
            market_value = price * h.shares

        total += market_value
        by_owner[h.owner] = by_owner.get(h.owner, 0.0) + market_value

        result_holdings.append(
            NetWorthHolding(
                symbol=h.symbol,
                owner=h.owner,
                holding_type=h.holding_type,
                shares=h.shares,
                avg_cost=h.avg_cost,
                current_price=price,
                market_value=market_value,
                pct_of_total=0.0,
            )
        )

    for rh in result_holdings:
        rh.pct_of_total = (rh.market_value / total * 100) if total > 0 else 0.0

    return NetWorthSummary(
        total_net_worth=total, holdings=result_holdings, by_owner=by_owner
    )


@router.get("/{holding_id}", response_model=HoldingOut)
def get_holding(holding_id: int, db: Session = Depends(get_db)):
    h = db.get(Holding, holding_id)
    if not h:
        raise HTTPException(404, "Holding not found")
    return h


@router.put("/{holding_id}", response_model=HoldingOut)
def update_holding(
    holding_id: int, payload: HoldingUpdate, db: Session = Depends(get_db)
):
    h = db.get(Holding, holding_id)
    if not h:
        raise HTTPException(404, "Holding not found")
    for key, val in payload.model_dump(exclude_unset=True).items():
        setattr(h, key, val)
    db.commit()
    db.refresh(h)
    return h


@router.delete("/{holding_id}", status_code=204)
def delete_holding(holding_id: int, db: Session = Depends(get_db)):
    h = db.get(Holding, holding_id)
    if not h:
        raise HTTPException(404, "Holding not found")
    db.delete(h)
    db.commit()


@router.post("/import-csv", response_model=CSVImportResult)
async def import_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Import holdings from CSV.  Expected columns:
      symbol, shares, avg_cost, owner, holding_type, strike, expiry, option_type, tags
    """
    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    imported = 0
    skipped = 0
    errors: List[str] = []

    for i, row in enumerate(reader, start=2):
        try:
            symbol = row["symbol"].strip().upper()
            shares = int(row["shares"])
            avg_cost = float(row["avg_cost"])
            owner = row.get("owner", "Venky").strip()
            if owner not in ("Venky", "Bharg"):
                owner = "Venky"
            holding_type = row.get("holding_type", "stock").strip().lower()
            if holding_type not in ("stock", "leaps"):
                holding_type = "stock"
            strike = float(row["strike"]) if row.get("strike") else None
            expiry = row.get("expiry", "").strip() or None
            option_type = row.get("option_type", "").strip().lower() or None
            if option_type and option_type not in ("call", "put"):
                option_type = None
            tags = row.get("tags", "").strip() or None

            h = Holding(
                symbol=symbol,
                shares=shares,
                avg_cost=avg_cost,
                owner=owner,
                holding_type=holding_type,
                strike=strike,
                expiry=expiry,
                option_type=option_type,
                tags=tags,
            )
            db.add(h)
            imported += 1
        except Exception as exc:
            errors.append(f"Row {i}: {exc}")
            skipped += 1

    db.commit()
    return CSVImportResult(imported=imported, skipped=skipped, errors=errors)


@router.post("/demo", response_model=List[HoldingOut])
def load_demo(db: Session = Depends(get_db)):
    """Insert sample holdings for TSLA, META, QQQ."""
    demos = [
        Holding(symbol="TSLA", shares=200, avg_cost=250.00, owner="Venky", tags="growth"),
        Holding(symbol="META", shares=100, avg_cost=480.00, owner="Venky", tags="tech"),
        Holding(symbol="QQQ", shares=300, avg_cost=440.00, owner="Bharg", tags="index"),
    ]
    db.add_all(demos)
    db.commit()
    for d in demos:
        db.refresh(d)
    return demos
