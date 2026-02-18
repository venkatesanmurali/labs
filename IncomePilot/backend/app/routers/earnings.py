"""
Earnings Time analysis router.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.engines.earnings_engine import analyze_earnings
from app.schemas.earnings import EarningsAnalysisResponse

router = APIRouter(prefix="/api/earnings", tags=["earnings"])


@router.get("/analyze/{symbol}", response_model=EarningsAnalysisResponse)
def get_earnings_analysis(symbol: str):
    """Analyze a stock before earnings using AI."""
    try:
        return analyze_earnings(symbol)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")
