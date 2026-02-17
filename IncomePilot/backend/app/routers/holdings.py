"""Holdings CRUD + CSV import router."""

from __future__ import annotations

import csv
import io
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.holding import Holding
from app.schemas.holding import (
    CSVImportResult,
    HoldingCreate,
    HoldingOut,
    HoldingUpdate,
)

router = APIRouter(prefix="/api/holdings", tags=["holdings"])


@router.get("", response_model=List[HoldingOut])
def list_holdings(db: Session = Depends(get_db)):
    return db.query(Holding).order_by(Holding.symbol).all()


@router.post("", response_model=HoldingOut, status_code=201)
def create_holding(payload: HoldingCreate, db: Session = Depends(get_db)):
    h = Holding(**payload.model_dump())
    db.add(h)
    db.commit()
    db.refresh(h)
    return h


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
      symbol, shares, avg_cost, account_type, tags
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
            acct = row.get("account_type", "taxable").strip().lower()
            if acct not in ("taxable", "retirement"):
                acct = "taxable"
            tags = row.get("tags", "").strip() or None

            h = Holding(
                symbol=symbol,
                shares=shares,
                avg_cost=avg_cost,
                account_type=acct,
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
        Holding(symbol="TSLA", shares=200, avg_cost=250.00, account_type="taxable", tags="growth"),
        Holding(symbol="META", shares=100, avg_cost=480.00, account_type="taxable", tags="tech"),
        Holding(symbol="QQQ", shares=300, avg_cost=440.00, account_type="retirement", tags="index"),
    ]
    db.add_all(demos)
    db.commit()
    for d in demos:
        db.refresh(d)
    return demos
