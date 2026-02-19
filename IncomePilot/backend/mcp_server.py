"""
IncomePilot MCP Server

Exposes portfolio data, market quotes, earnings analysis, and trade history
as MCP tools that AI assistants (Claude Desktop, Claude Code) can call.

Usage:
  stdio (Claude Desktop / Claude Code):
    python mcp_server.py

  HTTP (web / inspector):
    python mcp_server.py --http

Register with Claude Code:
  claude mcp add incomepilot -- python /path/to/mcp_server.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from typing import Annotated, Optional

from pydantic import Field
from mcp.server.fastmcp import FastMCP

# ── Bootstrap: ensure app imports work ──────────────────────────────────
# This file lives in backend/ alongside the app/ package.
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import get_settings
from app.database import SessionLocal
from app.models.holding import Holding
from app.models.option_trade import OptionTrade
from app.providers import get_provider

# ── Create MCP Server ──────────────────────────────────────────────────
mcp = FastMCP(name="incomepilot")


def _get_db():
    """Get a DB session (not a generator, just a plain session)."""
    return SessionLocal()


# ═══════════════════════════════════════════════════════════════════════
# TOOL 1: Get Portfolio Holdings
# ═══════════════════════════════════════════════════════════════════════

@mcp.tool()
def get_portfolio(
    owner: Annotated[Optional[str], Field(description="Filter by owner: 'Venky' or 'Bharg'. Leave empty for all.")] = None,
) -> str:
    """Get all portfolio holdings (stocks and LEAPS options), optionally filtered by owner."""
    db = _get_db()
    try:
        q = db.query(Holding)
        if owner:
            q = q.filter(Holding.owner == owner)
        holdings = q.order_by(Holding.symbol).all()

        if not holdings:
            return "No holdings found."

        results = []
        for h in holdings:
            entry = {
                "symbol": h.symbol,
                "shares": h.shares,
                "avg_cost": h.avg_cost,
                "owner": h.owner,
                "type": h.holding_type,
            }
            if h.holding_type == "leaps":
                entry["strike"] = h.strike
                entry["expiry"] = str(h.expiry)
                entry["option_type"] = h.option_type
            if h.tags:
                entry["tags"] = h.tags
            results.append(entry)

        return json.dumps(results, indent=2)
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════
# TOOL 2: Get Net Worth
# ═══════════════════════════════════════════════════════════════════════

@mcp.tool()
def get_net_worth() -> str:
    """Calculate total portfolio net worth with current market prices, broken down by owner."""
    db = _get_db()
    try:
        holdings = db.query(Holding).all()
        if not holdings:
            return "No holdings found."

        provider = get_provider()
        symbols = list({h.symbol for h in holdings})
        prices = {}
        for sym in symbols:
            try:
                quote = provider.get_quote(sym)
                prices[sym] = quote.price
            except Exception:
                prices[sym] = 0.0

        total = 0.0
        by_owner: dict[str, float] = {}
        details = []

        for h in holdings:
            price = prices.get(h.symbol, 0.0)
            if h.holding_type == "leaps" and h.strike:
                intrinsic = max(0.0, price - h.strike) if h.option_type == "call" else max(0.0, h.strike - price)
                market_value = intrinsic * 100 * h.shares
            else:
                market_value = price * h.shares

            total += market_value
            by_owner[h.owner] = by_owner.get(h.owner, 0.0) + market_value
            details.append({
                "symbol": h.symbol,
                "owner": h.owner,
                "type": h.holding_type,
                "shares": h.shares,
                "current_price": round(price, 2),
                "market_value": round(market_value, 2),
            })

        result = {
            "total_net_worth": round(total, 2),
            "by_owner": {k: round(v, 2) for k, v in by_owner.items()},
            "holdings": details,
        }
        return json.dumps(result, indent=2)
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════
# TOOL 3: Get Stock Quote
# ═══════════════════════════════════════════════════════════════════════

@mcp.tool()
def get_stock_quote(
    symbol: Annotated[str, Field(description="Ticker symbol, e.g. AAPL, TSLA, VOO")],
) -> str:
    """Get the current market price for a stock or ETF."""
    provider = get_provider()
    try:
        quote = provider.get_quote(symbol.upper())
        return json.dumps({
            "symbol": quote.symbol,
            "price": quote.price,
            "timestamp": quote.timestamp,
        }, indent=2)
    except Exception as e:
        return f"Error fetching quote for {symbol}: {e}"


# ═══════════════════════════════════════════════════════════════════════
# TOOL 4: Analyze Earnings (AI-powered)
# ═══════════════════════════════════════════════════════════════════════

@mcp.tool()
def analyze_earnings(
    symbol: Annotated[str, Field(description="Ticker symbol to analyze before earnings, e.g. AAPL, TSLA")],
) -> str:
    """Run a deep AI-powered analysis of a stock before its earnings report.

    Returns prediction (UP/DOWN with confidence), options recommendation,
    key financial metrics, and risk factors. Uses real Yahoo Finance data
    and Claude for analysis. May take 10-15 seconds.
    """
    from app.engines.earnings_engine import analyze_earnings as _analyze

    try:
        result = _analyze(symbol.upper())
        return result.model_dump_json(indent=2)
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Analysis failed: {e}"


# ═══════════════════════════════════════════════════════════════════════
# TOOL 5: Get Trade History
# ═══════════════════════════════════════════════════════════════════════

@mcp.tool()
def get_trades(
    symbol: Annotated[Optional[str], Field(description="Filter by ticker symbol")] = None,
    owner: Annotated[Optional[str], Field(description="Filter by owner: 'Venky' or 'Bharg'")] = None,
    strategy_type: Annotated[Optional[str], Field(description="Filter by strategy: 'CC', 'CSP', or 'STOCK'")] = None,
    limit: Annotated[int, Field(description="Max number of trades to return", ge=1, le=500)] = 50,
) -> str:
    """Get option trade history with optional filters."""
    db = _get_db()
    try:
        q = db.query(OptionTrade).order_by(OptionTrade.trade_date.desc())
        if symbol:
            q = q.filter(OptionTrade.symbol == symbol.upper())
        if owner:
            q = q.filter(OptionTrade.owner == owner)
        if strategy_type:
            q = q.filter(OptionTrade.strategy_type == strategy_type.upper())
        trades = q.limit(limit).all()

        if not trades:
            return "No trades found."

        results = []
        for t in trades:
            entry = {
                "symbol": t.symbol,
                "strategy": t.strategy_type,
                "trade_type": t.trade_type,
                "premium": t.premium,
                "contracts": t.contracts,
                "trade_date": str(t.trade_date),
                "owner": t.owner,
            }
            if t.strike:
                entry["strike"] = t.strike
            if t.expiry:
                entry["expiry"] = str(t.expiry)
            if t.notes:
                entry["notes"] = t.notes
            results.append(entry)

        return json.dumps(results, indent=2)
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════
# TOOL 6: Get YTD P&L Summary
# ═══════════════════════════════════════════════════════════════════════

@mcp.tool()
def get_ytd_pnl(
    owner: Annotated[Optional[str], Field(description="Filter by owner: 'Venky' or 'Bharg'")] = None,
) -> str:
    """Get year-to-date profit & loss summary from option trades."""
    db = _get_db()
    try:
        year_start = datetime(datetime.now().year, 1, 1).date()
        q = db.query(OptionTrade).filter(OptionTrade.trade_date >= year_start)
        if owner:
            q = q.filter(OptionTrade.owner == owner)
        trades = q.all()

        total_premium = 0.0
        total_losses = 0.0
        count = 0

        for t in trades:
            count += 1
            if t.premium >= 0:
                total_premium += t.premium * t.contracts
            else:
                total_losses += t.premium * t.contracts

        result = {
            "year": datetime.now().year,
            "total_premium_collected": round(total_premium, 2),
            "total_losses": round(total_losses, 2),
            "net_pnl": round(total_premium + total_losses, 2),
            "trade_count": count,
        }
        if owner:
            result["owner"] = owner

        return json.dumps(result, indent=2)
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════
# Entry Point
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if "--http" in sys.argv:
        print("Starting IncomePilot MCP server on http://localhost:9000/mcp",
              file=sys.stderr)
        mcp.run(transport="streamable-http", host="127.0.0.1", port=9000)
    else:
        mcp.run(transport="stdio")
