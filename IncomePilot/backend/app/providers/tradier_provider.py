"""
Tradier market-data provider using the Tradier REST API.

Tradier offers a free "sandbox" tier that provides delayed options data.
Production accounts get real-time data.

Usage:
  1. Sign up at https://developer.tradier.com/
  2. Set in .env:
     MARKET_DATA_PROVIDER=tradier
     TRADIER_API_KEY=your-api-key
     TRADIER_SANDBOX=true   # use sandbox endpoint (default: true)
"""

from __future__ import annotations

import logging
import math
from datetime import date, datetime
from typing import Optional

import httpx

from app.providers.base import MarketDataProvider
from app.schemas.market_data import (
    EarningsDate,
    OptionChain,
    OptionContract,
    Quote,
)

logger = logging.getLogger(__name__)

_PROD_BASE = "https://api.tradier.com/v1"
_SANDBOX_BASE = "https://sandbox.tradier.com/v1"


class TradierProvider(MarketDataProvider):
    """Fetches live market data from the Tradier brokerage API."""

    def __init__(self, api_key: str, sandbox: bool = True):
        self.api_key = api_key
        self.base_url = _SANDBOX_BASE if sandbox else _PROD_BASE
        self._headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }

    def _get(self, path: str, params: dict | None = None) -> dict:
        url = f"{self.base_url}{path}"
        with httpx.Client(timeout=15) as client:
            resp = client.get(url, headers=self._headers, params=params or {})
            resp.raise_for_status()
            return resp.json()

    # ── Quote ──────────────────────────────────────────────────────────────

    def get_quote(self, symbol: str) -> Quote:
        data = self._get("/markets/quotes", {"symbols": symbol.upper()})
        quotes = data.get("quotes", {})
        q = quotes.get("quote", {})
        if isinstance(q, list):
            q = q[0]
        price = float(q.get("last", 0) or q.get("close", 0) or 0)
        return Quote(symbol=symbol.upper(), price=price, timestamp=datetime.utcnow())

    # ── Option chain ──────────────────────────────────────────────────────

    def get_option_chain(
        self, symbol: str, as_of_date: Optional[date] = None
    ) -> OptionChain:
        sym = symbol.upper()
        today = as_of_date or date.today()

        # Step 1: Get spot price
        quote = self.get_quote(sym)
        spot = quote.price

        # Step 2: Fetch available expirations
        exp_data = self._get(
            "/markets/options/expirations", {"symbol": sym, "includeAllRoots": "true"}
        )
        expirations_raw = (
            exp_data.get("expirations", {}).get("date", [])
        )
        if isinstance(expirations_raw, str):
            expirations_raw = [expirations_raw]

        contracts: list[OptionContract] = []

        for exp_str in expirations_raw:
            exp_date = date.fromisoformat(exp_str)
            dte = (exp_date - today).days
            if dte < 1 or dte > 60:
                continue

            # Step 3: Fetch chain for this expiration
            try:
                chain_data = self._get(
                    "/markets/options/chains",
                    {
                        "symbol": sym,
                        "expiration": exp_str,
                        "greeks": "true",
                    },
                )
            except Exception:
                logger.warning("Failed to fetch Tradier chain %s exp %s", sym, exp_str)
                continue

            options = chain_data.get("options", {}).get("option", [])
            if isinstance(options, dict):
                options = [options]

            for opt in options:
                opt_type = opt.get("option_type")
                if opt_type not in ("call", "put"):
                    continue

                strike = float(opt.get("strike", 0))
                bid = float(opt.get("bid", 0) or 0)
                ask = float(opt.get("ask", 0) or 0)
                last = float(opt.get("last", 0) or 0)
                mid = round((bid + ask) / 2, 2) if (bid + ask) > 0 else last
                oi = int(opt.get("open_interest", 0) or 0)
                vol = int(opt.get("volume", 0) or 0)

                # Greeks from Tradier
                greeks = opt.get("greeks") or {}
                delta = float(greeks.get("delta", 0) or 0)
                gamma = float(greeks.get("gamma", 0) or 0)
                theta = float(greeks.get("theta", 0) or 0)
                vega = float(greeks.get("vega", 0) or 0)
                iv = float(greeks.get("mid_iv", 0) or greeks.get("smv_vol", 0) or 0)

                contracts.append(
                    OptionContract(
                        symbol=sym,
                        expiry=exp_date,
                        strike=strike,
                        option_type=opt_type,
                        bid=bid,
                        ask=ask,
                        last=last,
                        mid=mid,
                        iv=iv,
                        delta=round(delta, 4),
                        gamma=round(gamma, 6),
                        theta=round(theta, 4),
                        vega=round(vega, 4),
                        open_interest=oi,
                        volume=vol,
                        dte=dte,
                    )
                )

        return OptionChain(
            symbol=sym,
            as_of=datetime.utcnow(),
            spot=spot,
            contracts=contracts,
        )

    # ── Earnings calendar ─────────────────────────────────────────────────

    def get_earnings_calendar(self, symbol: str) -> EarningsDate:
        sym = symbol.upper()
        try:
            data = self._get(
                "/markets/fundamentals/calendars",
                {"symbols": sym},
            )
            results = data.get("results", [])
            if isinstance(results, dict):
                results = [results]
            for result in results:
                tables = result.get("tables", {})
                corp_cal = tables.get("corporate_calendars")
                if not corp_cal:
                    continue
                rows = corp_cal.get("rows", [])
                if isinstance(rows, dict):
                    rows = [rows]
                today = date.today()
                for row in rows:
                    event = row.get("event", "")
                    if "earning" not in event.lower():
                        continue
                    begin = row.get("begin_date_time", "")
                    if begin:
                        ed = date.fromisoformat(begin[:10])
                        if ed >= today:
                            return EarningsDate(symbol=sym, next_earnings=ed)
        except Exception:
            logger.warning("Could not fetch Tradier earnings for %s", sym)

        return EarningsDate(symbol=sym, next_earnings=None)
