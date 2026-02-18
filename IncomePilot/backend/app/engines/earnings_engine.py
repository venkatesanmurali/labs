"""
Earnings Time analysis engine.

Fetches comprehensive financial data via yfinance and uses Claude API
for intelligent prediction of post-earnings price movement.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

import anthropic
import yfinance as yf

from app.config import get_settings
from app.schemas.earnings import (
    AnalystTargets,
    EarningsAnalysisResponse,
    EPSQuarter,
    Financials,
    KeyMetric,
    OptionsRecommendation,
    Prediction,
    RevenueQuarter,
)

logger = logging.getLogger(__name__)


def _safe(val: Any) -> Optional[float]:
    """Return a float or None, protecting against NaN/Inf."""
    if val is None:
        return None
    try:
        f = float(val)
        if f != f or f == float("inf") or f == float("-inf"):
            return None
        return round(f, 4)
    except (TypeError, ValueError):
        return None


def _fmt_large(val: Optional[float]) -> str:
    if val is None:
        return "N/A"
    abs_val = abs(val)
    if abs_val >= 1e12:
        return f"${val / 1e12:.2f}T"
    if abs_val >= 1e9:
        return f"${val / 1e9:.2f}B"
    if abs_val >= 1e6:
        return f"${val / 1e6:.1f}M"
    return f"${val:,.0f}"


def fetch_financial_data(symbol: str) -> dict:
    """Fetch comprehensive financial data from Yahoo Finance."""
    ticker = yf.Ticker(symbol)
    info = ticker.info or {}

    # ── Basic info ──
    data: dict[str, Any] = {
        "company_name": info.get("longName") or info.get("shortName") or symbol,
        "current_price": _safe(info.get("currentPrice") or info.get("regularMarketPrice")),
        "market_cap": _safe(info.get("marketCap")),
        "pe_ratio": _safe(info.get("trailingPE")),
        "forward_pe": _safe(info.get("forwardPE")),
        "ebitda": _safe(info.get("ebitda")),
        "profit_margin": _safe(info.get("profitMargins")),
        "debt_to_equity": _safe(info.get("debtToEquity")),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
    }

    # ── Earnings date ──
    try:
        cal = ticker.calendar
        if cal is not None:
            if isinstance(cal, dict) and "Earnings Date" in cal:
                dates = cal["Earnings Date"]
                if dates:
                    data["earnings_date"] = str(dates[0])
            elif hasattr(cal, "iloc"):
                data["earnings_date"] = str(cal.iloc[0, 0]) if cal.shape[0] > 0 else None
    except Exception:
        data["earnings_date"] = None

    # ── EPS history ──
    eps_history: list[dict] = []
    try:
        earnings_hist = ticker.earnings_history
        if earnings_hist is not None and not earnings_hist.empty:
            for _, row in earnings_hist.iterrows():
                actual = _safe(row.get("epsActual"))
                estimate = _safe(row.get("epsEstimate"))
                surprise = _safe(row.get("surprisePercent"))
                quarter_str = str(row.get("quarter", ""))
                beat = None
                if actual is not None and estimate is not None:
                    beat = actual >= estimate
                eps_history.append({
                    "quarter": quarter_str,
                    "actual": actual,
                    "estimate": estimate,
                    "surprise_pct": surprise,
                    "beat": beat,
                })
    except Exception:
        pass
    # Fallback: try earnings_dates
    if not eps_history:
        try:
            eh = ticker.get_earnings_history()
            if eh:
                for item in eh:
                    actual = _safe(item.get("epsActual"))
                    estimate = _safe(item.get("epsEstimate"))
                    eps_history.append({
                        "quarter": str(item.get("quarter", "")),
                        "actual": actual,
                        "estimate": estimate,
                        "surprise_pct": _safe(item.get("surprisePercent")),
                        "beat": actual >= estimate if actual is not None and estimate is not None else None,
                    })
        except Exception:
            pass
    data["eps_history"] = eps_history[-8:]  # last 8 quarters max

    # ── Revenue history ──
    revenue_history: list[dict] = []
    try:
        q_financials = ticker.quarterly_financials
        if q_financials is not None and not q_financials.empty:
            rev_row = None
            for label in ["Total Revenue", "Revenue"]:
                if label in q_financials.index:
                    rev_row = q_financials.loc[label]
                    break
            if rev_row is not None:
                sorted_cols = sorted(rev_row.index)
                for i, col in enumerate(sorted_cols):
                    rev = _safe(rev_row[col])
                    yoy = None
                    if i >= 4:
                        prev = _safe(rev_row[sorted_cols[i - 4]])
                        if prev and prev != 0 and rev is not None:
                            yoy = round(((rev - prev) / abs(prev)) * 100, 2)
                    revenue_history.append({
                        "quarter": str(col.date()) if hasattr(col, "date") else str(col),
                        "revenue": rev,
                        "yoy_growth_pct": yoy,
                    })
    except Exception:
        pass
    data["revenue_history"] = revenue_history[-8:]

    # ── Analyst targets ──
    data["analyst_targets"] = {
        "low": _safe(info.get("targetLowPrice")),
        "median": _safe(info.get("targetMedianPrice")),
        "high": _safe(info.get("targetHighPrice")),
        "number_of_analysts": info.get("numberOfAnalystOpinions"),
    }

    # ── Analyst recommendations ──
    data["recommendation_distribution"] = {}
    try:
        recs = ticker.recommendations
        if recs is not None and not recs.empty:
            recent = recs.tail(1)
            if not recent.empty:
                row = recent.iloc[0]
                data["recommendation_distribution"] = {
                    k: int(v) for k, v in row.items() if k != "period"
                }
    except Exception:
        pass

    # ── Price action ──
    try:
        hist = ticker.history(period="6mo")
        if hist is not None and not hist.empty:
            current = hist["Close"].iloc[-1]
            if len(hist) >= 22:
                p30 = hist["Close"].iloc[-22]
                data["price_change_30d_pct"] = round(((current - p30) / p30) * 100, 2)
            if len(hist) >= 63:
                p90 = hist["Close"].iloc[-63]
                data["price_change_90d_pct"] = round(((current - p90) / p90) * 100, 2)
    except Exception:
        pass

    # ── Implied volatility (ATM options) ──
    try:
        exp_dates = ticker.options
        if exp_dates:
            chain = ticker.option_chain(exp_dates[0])
            if chain and chain.calls is not None and not chain.calls.empty:
                price = data["current_price"] or 0
                calls = chain.calls
                calls = calls[calls["impliedVolatility"] > 0]
                if not calls.empty:
                    calls["dist"] = (calls["strike"] - price).abs()
                    atm = calls.loc[calls["dist"].idxmin()]
                    data["implied_volatility"] = round(float(atm["impliedVolatility"]) * 100, 2)
    except Exception:
        pass

    return data


def _build_prompt(data: dict) -> str:
    """Build the analysis prompt for Claude."""
    eps_text = ""
    for q in data.get("eps_history", []):
        beat_str = "BEAT" if q.get("beat") else ("MISS" if q.get("beat") is False else "N/A")
        eps_text += f"  {q['quarter']}: Actual={q.get('actual', 'N/A')}, Est={q.get('estimate', 'N/A')}, Surprise={q.get('surprise_pct', 'N/A')}%, {beat_str}\n"

    rev_text = ""
    for q in data.get("revenue_history", []):
        rev_text += f"  {q['quarter']}: Revenue={_fmt_large(q.get('revenue'))}, YOY Growth={q.get('yoy_growth_pct', 'N/A')}%\n"

    targets = data.get("analyst_targets", {})
    recs = data.get("recommendation_distribution", {})

    return f"""You are a senior equity research analyst. Analyze the following financial data for {data['company_name']} ({data.get('ticker', '')}) before their upcoming earnings report and provide a prediction.

## Current Market Data
- Current Price: ${data.get('current_price', 'N/A')}
- Market Cap: {_fmt_large(data.get('market_cap'))}
- P/E Ratio: {data.get('pe_ratio', 'N/A')}
- Forward P/E: {data.get('forward_pe', 'N/A')}
- EBITDA: {_fmt_large(data.get('ebitda'))}
- Profit Margin: {f"{data['profit_margin']*100:.1f}%" if data.get('profit_margin') else 'N/A'}
- Debt/Equity: {data.get('debt_to_equity', 'N/A')}
- Sector: {data.get('sector', 'N/A')}
- Industry: {data.get('industry', 'N/A')}
- Earnings Date: {data.get('earnings_date', 'N/A')}

## EPS History (Recent Quarters)
{eps_text or '  No data available'}

## Revenue History
{rev_text or '  No data available'}

## Analyst Targets
- Low: ${targets.get('low', 'N/A')} | Median: ${targets.get('median', 'N/A')} | High: ${targets.get('high', 'N/A')}
- Number of Analysts: {targets.get('number_of_analysts', 'N/A')}

## Analyst Recommendations
{json.dumps(recs, indent=2) if recs else 'No data available'}

## Price Action
- 30-day change: {data.get('price_change_30d_pct', 'N/A')}%
- 90-day change: {data.get('price_change_90d_pct', 'N/A')}%

## Options Data
- Implied Volatility: {data.get('implied_volatility', 'N/A')}%

Based on this data, provide your analysis in the following JSON format. Be specific and data-driven:

{{
  "prediction": {{
    "direction": "UP" or "DOWN",
    "magnitude_pct": <expected % move, e.g. 5.2>,
    "confidence": <1-100>
  }},
  "options_recommendation": {{
    "viable": true/false,
    "strategy": "CALL" or "PUT" or null,
    "suggested_strike": <strike price or null>,
    "suggested_expiry": "<YYYY-MM-DD or null>",
    "rationale": "<brief explanation>"
  }},
  "key_metrics": [
    {{"name": "<metric name>", "value": "<display value>", "sentiment": "bullish" or "bearish" or "neutral"}},
    ... (provide 6-10 key metrics)
  ],
  "risk_factors": [
    "<risk 1>",
    "<risk 2>",
    ... (3-5 risks)
  ],
  "analysis_summary": "<Detailed 2-4 paragraph markdown analysis covering earnings surprise probability, valuation, momentum, and your thesis>"
}}

Important:
- Base your prediction on the EPS beat/miss pattern, revenue trajectory, valuation, and market sentiment
- For options, consider IV levels - if IV is very high, spreads may be better than directional plays
- suggested_strike should be a realistic strike near the money
- suggested_expiry should be the nearest weekly/monthly expiry after earnings
- Be honest about confidence - if data is limited, confidence should be lower
- Return ONLY valid JSON, no other text"""


def analyze_earnings(symbol: str) -> EarningsAnalysisResponse:
    """Run full earnings analysis: fetch data + AI prediction."""
    settings = get_settings()

    if not settings.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY not configured. Add it to your .env file.")

    # Fetch financial data
    data = fetch_financial_data(symbol.upper())
    data["ticker"] = symbol.upper()

    if data["current_price"] is None:
        raise ValueError(f"Could not fetch price data for {symbol}. Check the ticker symbol.")

    # Call Claude
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    prompt = _build_prompt(data)

    message = client.messages.create(
        model=settings.ai_model,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = message.content[0].text.strip()

    # Parse JSON from response (handle markdown code blocks)
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        lines = [l for l in lines if not l.startswith("```")]
        response_text = "\n".join(lines)

    try:
        result = json.loads(response_text)
    except json.JSONDecodeError:
        # Try to extract JSON from the response
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        if start >= 0 and end > start:
            result = json.loads(response_text[start:end])
        else:
            raise ValueError("Failed to parse AI response as JSON")

    # Build response
    pred = result["prediction"]
    current_price = data["current_price"]
    magnitude_pct = pred["magnitude_pct"]
    magnitude_price = round(current_price * magnitude_pct / 100, 2)

    opts = result.get("options_recommendation", {})

    return EarningsAnalysisResponse(
        ticker=symbol.upper(),
        company_name=data["company_name"],
        current_price=current_price,
        earnings_date=data.get("earnings_date"),
        financials=Financials(
            eps_history=[EPSQuarter(**q) for q in data.get("eps_history", [])],
            revenue_history=[RevenueQuarter(**q) for q in data.get("revenue_history", [])],
            pe_ratio=data.get("pe_ratio"),
            forward_pe=data.get("forward_pe"),
            market_cap=data.get("market_cap"),
            ebitda=data.get("ebitda"),
            profit_margin=data.get("profit_margin"),
            debt_to_equity=data.get("debt_to_equity"),
            analyst_targets=AnalystTargets(**data.get("analyst_targets", {})) if data.get("analyst_targets") else None,
            recommendation_distribution=data.get("recommendation_distribution"),
            price_change_30d_pct=data.get("price_change_30d_pct"),
            price_change_90d_pct=data.get("price_change_90d_pct"),
            implied_volatility=data.get("implied_volatility"),
            sector=data.get("sector"),
            industry=data.get("industry"),
        ),
        prediction=Prediction(
            direction=pred["direction"],
            magnitude_pct=magnitude_pct,
            magnitude_price=magnitude_price,
            confidence=pred["confidence"],
        ),
        options_recommendation=OptionsRecommendation(
            viable=opts.get("viable", False),
            strategy=opts.get("strategy"),
            suggested_strike=opts.get("suggested_strike"),
            suggested_expiry=opts.get("suggested_expiry"),
            rationale=opts.get("rationale"),
        ),
        analysis_summary=result.get("analysis_summary", ""),
        key_metrics=[KeyMetric(**m) for m in result.get("key_metrics", [])],
        risk_factors=result.get("risk_factors", []),
    )
