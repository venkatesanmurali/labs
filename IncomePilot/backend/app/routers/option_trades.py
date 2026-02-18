"""Option trades CRUD + income report + YTD P&L router."""

from __future__ import annotations

import csv
import io
from collections import defaultdict
from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.option_trade import OptionTrade
from app.schemas.option_trade import (
    OptionTradeCreate,
    OptionTradeOut,
    OptionTradeUpdate,
    TradeCSVImportResult,
)
from app.schemas.analytics import IncomeReport, MonthlyIncome, YTDPnL

router = APIRouter(prefix="/api/trades", tags=["trades"])


@router.get("", response_model=List[OptionTradeOut])
def list_trades(
    symbol: Optional[str] = None,
    strategy_type: Optional[str] = Query(None, pattern=r"^(CC|CSP|STOCK)$"),
    owner: Optional[str] = Query(None, pattern=r"^(Venky|Bharg)$"),
    month: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}$"),  # YYYY-MM
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    q = db.query(OptionTrade)
    if symbol:
        q = q.filter(OptionTrade.symbol == symbol.upper())
    if strategy_type:
        q = q.filter(OptionTrade.strategy_type == strategy_type)
    if owner:
        q = q.filter(OptionTrade.owner == owner)
    if month:
        year, mon = int(month[:4]), int(month[5:])
        month_start = date(year, mon, 1)
        if mon == 12:
            month_end = date(year + 1, 1, 1)
        else:
            month_end = date(year, mon + 1, 1)
        q = q.filter(
            and_(OptionTrade.trade_date >= month_start, OptionTrade.trade_date < month_end)
        )
    if start_date:
        q = q.filter(OptionTrade.trade_date >= start_date)
    if end_date:
        q = q.filter(OptionTrade.trade_date <= end_date)
    return q.order_by(OptionTrade.trade_date.desc()).all()


@router.post("", response_model=OptionTradeOut, status_code=201)
def create_trade(payload: OptionTradeCreate, db: Session = Depends(get_db)):
    t = OptionTrade(**payload.model_dump(exclude={"avg_cost"}))
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@router.get("/income-report", response_model=IncomeReport)
def income_report(
    start_date: date = Query(...),
    end_date: date = Query(...),
    owner: Optional[str] = Query(None, pattern=r"^(Venky|Bharg)$"),
    db: Session = Depends(get_db),
):
    q = db.query(OptionTrade).filter(
        and_(
            OptionTrade.trade_date >= start_date,
            OptionTrade.trade_date <= end_date,
        )
    )
    if owner:
        q = q.filter(OptionTrade.owner == owner)
    trades = q.all()

    monthly: dict[str, dict] = defaultdict(
        lambda: {"cc_income": 0.0, "csp_income": 0.0, "stock_pnl": 0.0, "trade_count": 0}
    )

    for t in trades:
        month_key = t.trade_date.strftime("%Y-%m")
        if t.strategy_type == "STOCK":
            total = t.premium  # already (sell - avg_cost) * shares
        else:
            total = t.premium * t.contracts * 100
        if t.strategy_type == "CC":
            monthly[month_key]["cc_income"] += total
        elif t.strategy_type == "CSP":
            monthly[month_key]["csp_income"] += total
        else:
            monthly[month_key]["stock_pnl"] += total
        monthly[month_key]["trade_count"] += 1

    breakdown = []
    for month in sorted(monthly.keys()):
        m = monthly[month]
        month_total = m["cc_income"] + m["csp_income"] + m["stock_pnl"]
        breakdown.append(
            MonthlyIncome(
                month=month,
                cc_income=round(m["cc_income"], 2),
                csp_income=round(m["csp_income"], 2),
                stock_pnl=round(m["stock_pnl"], 2),
                total_income=round(month_total, 2),
                trade_count=m["trade_count"],
            )
        )

    cc_total = sum(b.cc_income for b in breakdown)
    csp_total = sum(b.csp_income for b in breakdown)
    stock_total = sum(b.stock_pnl for b in breakdown)

    return IncomeReport(
        start_date=str(start_date),
        end_date=str(end_date),
        monthly_breakdown=breakdown,
        totals={
            "cc_total": round(cc_total, 2),
            "csp_total": round(csp_total, 2),
            "stock_total": round(stock_total, 2),
        },
        grand_total=round(cc_total + csp_total + stock_total, 2),
    )


@router.get("/ytd-pnl", response_model=YTDPnL)
def ytd_pnl(
    owner: Optional[str] = Query(None, pattern=r"^(Venky|Bharg)$"),
    db: Session = Depends(get_db),
):
    year_start = date(date.today().year, 1, 1)
    q = db.query(OptionTrade).filter(OptionTrade.trade_date >= year_start)
    if owner:
        q = q.filter(OptionTrade.owner == owner)
    trades = q.all()

    total_income = 0.0
    total_losses = 0.0
    for t in trades:
        if t.strategy_type == "STOCK":
            total = t.premium  # already (sell - avg_cost) * shares
        else:
            total = t.premium * t.contracts * 100
        if total >= 0:
            total_income += total
        else:
            total_losses += total

    return YTDPnL(
        total_premium_collected=round(total_income, 2),
        total_losses=round(total_losses, 2),
        net_pnl=round(total_income + total_losses, 2),
        trade_count=len(trades),
    )


@router.get("/{trade_id}", response_model=OptionTradeOut)
def get_trade(trade_id: int, db: Session = Depends(get_db)):
    t = db.get(OptionTrade, trade_id)
    if not t:
        raise HTTPException(404, "Trade not found")
    return t


@router.put("/{trade_id}", response_model=OptionTradeOut)
def update_trade(
    trade_id: int, payload: OptionTradeUpdate, db: Session = Depends(get_db)
):
    t = db.get(OptionTrade, trade_id)
    if not t:
        raise HTTPException(404, "Trade not found")
    for key, val in payload.model_dump(exclude_unset=True).items():
        setattr(t, key, val)
    db.commit()
    db.refresh(t)
    return t


@router.delete("/{trade_id}", status_code=204)
def delete_trade(trade_id: int, db: Session = Depends(get_db)):
    t = db.get(OptionTrade, trade_id)
    if not t:
        raise HTTPException(404, "Trade not found")
    db.delete(t)
    db.commit()


# Contracts lookup: (owner, symbol) -> contracts count
CONTRACTS_LOOKUP: dict[tuple[str, str], int] = {
    ("Venky", "TSLA"): 11,
    ("Venky", "GOOGL"): 3,
    ("Venky", "GOOG"): 3,
    ("Bharg", "TSLA"): 7,
    ("Bharg", "GOOGL"): 4,
    ("Bharg", "GOOG"): 4,
}


def _parse_date_str(raw: str) -> str:
    """Parse date from DD/MM/YYYY or YYYY-MM-DD to YYYY-MM-DD."""
    raw = raw.strip()
    if "/" in raw:
        return datetime.strptime(raw, "%d/%m/%Y").strftime("%Y-%m-%d")
    return raw


@router.post("/import-csv", response_model=TradeCSVImportResult)
async def import_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Import trades from CSV/TSV. Expected columns:
      Type, Stock, strategy type, Strike price, Expiry, Amount, Comments, Who
    Optional: Date (M/D/YYYY or YYYY-MM-DD, defaults to today)

    Amount = total premium (not per-contract). Contracts are derived from
    owner+symbol lookup; premium = Amount / (contracts * 100).
    """
    content = await file.read()
    text = content.decode("utf-8-sig")
    # Auto-detect delimiter: tab or comma
    delimiter = "\t" if "\t" in text.split("\n", 1)[0] else ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)

    imported = 0
    skipped = 0
    errors: List[str] = []

    for i, row in enumerate(reader, start=2):
        try:
            trade_type = row["Type"].strip().lower()
            if trade_type not in ("fresh", "roll"):
                raise ValueError(f"Invalid Type: {row['Type']}")
            symbol = row["Stock"].strip().upper()
            strategy_type = row["strategy type"].strip().upper()
            if strategy_type not in ("CC", "CSP"):
                raise ValueError(f"Invalid strategy type: {strategy_type}")
            strike = float(row["Strike price"])
            expiry = datetime.strptime(_parse_date_str(row["Expiry"]), "%Y-%m-%d")
            amount = float(row["Amount"])
            owner = row["Who"].strip()
            if owner not in ("Venky", "Bharg"):
                owner = "Venky"
            notes = row.get("Comments", "").strip() or None

            # Derive contracts from lookup, default to 1
            contracts = CONTRACTS_LOOKUP.get((owner, symbol), 1)

            # Back-calculate per-contract premium from total amount
            premium = amount / (contracts * 100) if contracts > 0 else amount

            # Optional Date column, default to today
            raw_date = row.get("Date", "").strip()
            if raw_date:
                if "/" in raw_date:
                    trade_date = datetime.strptime(raw_date, "%d/%m/%Y").date()
                else:
                    trade_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
            else:
                trade_date = date.today()

            t = OptionTrade(
                symbol=symbol,
                strategy_type=strategy_type,
                trade_type=trade_type,
                strike=strike,
                expiry=expiry,
                premium=round(premium, 4),
                contracts=contracts,
                trade_date=trade_date,
                owner=owner,
                notes=notes,
            )
            db.add(t)
            imported += 1
        except Exception as exc:
            errors.append(f"Row {i}: {exc}")
            skipped += 1

    db.commit()
    return TradeCSVImportResult(imported=imported, skipped=skipped, errors=errors)
