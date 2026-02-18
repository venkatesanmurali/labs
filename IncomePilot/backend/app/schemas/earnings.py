"""
Pydantic schemas for the Earnings Time analysis feature.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class EPSQuarter(BaseModel):
    quarter: str
    actual: Optional[float] = None
    estimate: Optional[float] = None
    surprise_pct: Optional[float] = None
    beat: Optional[bool] = None


class RevenueQuarter(BaseModel):
    quarter: str
    revenue: Optional[float] = None
    yoy_growth_pct: Optional[float] = None


class AnalystTargets(BaseModel):
    low: Optional[float] = None
    median: Optional[float] = None
    high: Optional[float] = None
    number_of_analysts: Optional[int] = None


class Financials(BaseModel):
    eps_history: List[EPSQuarter] = []
    revenue_history: List[RevenueQuarter] = []
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    market_cap: Optional[float] = None
    ebitda: Optional[float] = None
    profit_margin: Optional[float] = None
    debt_to_equity: Optional[float] = None
    analyst_targets: Optional[AnalystTargets] = None
    recommendation_distribution: Optional[dict] = None
    price_change_30d_pct: Optional[float] = None
    price_change_90d_pct: Optional[float] = None
    implied_volatility: Optional[float] = None
    sector: Optional[str] = None
    industry: Optional[str] = None


class Prediction(BaseModel):
    direction: str  # "UP" or "DOWN"
    magnitude_pct: float
    magnitude_price: float
    confidence: int  # 1-100


class OptionsRecommendation(BaseModel):
    viable: bool
    strategy: Optional[str] = None  # "CALL" or "PUT"
    suggested_strike: Optional[float] = None
    suggested_expiry: Optional[str] = None
    rationale: Optional[str] = None


class KeyMetric(BaseModel):
    name: str
    value: str
    sentiment: str  # "bullish", "bearish", "neutral"


class EarningsAnalysisRequest(BaseModel):
    ticker: str


class EarningsAnalysisResponse(BaseModel):
    ticker: str
    company_name: str
    current_price: float
    earnings_date: Optional[str] = None
    financials: Financials
    prediction: Prediction
    options_recommendation: OptionsRecommendation
    analysis_summary: str
    key_metrics: List[KeyMetric] = []
    risk_factors: List[str] = []
