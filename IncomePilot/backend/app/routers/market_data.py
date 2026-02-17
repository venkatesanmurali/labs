"""Market data passthrough endpoints (for frontend to fetch quotes/chains)."""

from __future__ import annotations

from fastapi import APIRouter

from app.providers import get_provider
from app.schemas.market_data import EarningsDate, OptionChain, Quote

router = APIRouter(prefix="/api/market", tags=["market-data"])


@router.get("/quote/{symbol}", response_model=Quote)
def get_quote(symbol: str):
    return get_provider().get_quote(symbol.upper())


@router.get("/chain/{symbol}", response_model=OptionChain)
def get_chain(symbol: str):
    return get_provider().get_option_chain(symbol.upper())


@router.get("/earnings/{symbol}", response_model=EarningsDate)
def get_earnings(symbol: str):
    return get_provider().get_earnings_calendar(symbol.upper())
