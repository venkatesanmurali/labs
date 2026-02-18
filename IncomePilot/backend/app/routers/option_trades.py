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
    strategy_type: Optional[str] = Query(None, pattern=r"^(CC|CSP)$"),
    owner: Optional[str] = Query(None, pattern=r"^(Venky|Bharg)$"),
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
    if start_date:
        q = q.filter(OptionTrade.trade_date >= start_date)
    if end_date:
        q = q.filter(OptionTrade.trade_date <= end_date)
    return q.order_by(OptionTrade.trade_date.desc()).all()


@router.post("", response_model=OptionTradeOut, status_code=201)
def create_trade(payload: OptionTradeCreate, db: Session = Depends(get_db)):
    t = OptionTrade(**payload.model_dump())
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
        lambda: {"cc_income": 0.0, "csp_income": 0.0, "trade_count": 0}
    )

    for t in trades:
        month_key = t.trade_date.strftime("%Y-%m")
        total = t.premium * t.contracts * 100
        if t.strategy_type == "CC":
            monthly[month_key]["cc_income"] += total
        else:
            monthly[month_key]["csp_income"] += total
        monthly[month_key]["trade_count"] += 1

    breakdown = []
    for month in sorted(monthly.keys()):
        m = monthly[month]
        breakdown.append(
            MonthlyIncome(
                month=month,
                cc_income=round(m["cc_income"], 2),
                csp_income=round(m["csp_income"], 2),
                total_income=round(m["cc_income"] + m["csp_income"], 2),
                trade_count=m["trade_count"],
            )
        )

    cc_total = sum(b.cc_income for b in breakdown)
    csp_total = sum(b.csp_income for b in breakdown)

    return IncomeReport(
        start_date=str(start_date),
        end_date=str(end_date),
        monthly_breakdown=breakdown,
        totals={"cc_total": round(cc_total, 2), "csp_total": round(csp_total, 2)},
        grand_total=round(cc_total + csp_total, 2),
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


@router.post("/import-csv", response_model=TradeCSVImportResult)
async def import_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Import trades from CSV. Expected columns:
      trade_type, symbol, strategy_type, strike, expiry, premium, contracts, trade_date, owner, notes
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
            strategy_type = row["strategy_type"].strip().upper()
            if strategy_type not in ("CC", "CSP"):
                raise ValueError(f"Invalid strategy_type: {strategy_type}")
            trade_type = row["trade_type"].strip().lower()
            if trade_type not in ("fresh", "roll"):
                raise ValueError(f"Invalid trade_type: {trade_type}")
            strike = float(row["strike"])
            expiry = row["expiry"].strip()
            premium = float(row["premium"])
            contracts = int(row.get("contracts", "1").strip() or "1")
            trade_date = datetime.strptime(row["trade_date"].strip(), "%Y-%m-%d").date()
            owner = row.get("owner", "Venky").strip()
            if owner not in ("Venky", "Bharg"):
                owner = "Venky"
            notes = row.get("notes", "").strip() or None

            t = OptionTrade(
                symbol=symbol,
                strategy_type=strategy_type,
                trade_type=trade_type,
                strike=strike,
                expiry=expiry,
                premium=premium,
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
