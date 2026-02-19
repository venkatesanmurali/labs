"""
Mock market-data provider with realistic data for 5 NASDAQ tickers.

All data is deterministic (seeded from symbol + strike) so tests are repeatable.
Prices are roughly calibrated to Feb 2025 levels; the mock generates
a plausible option chain on the fly for any query date.
"""

from __future__ import annotations

import hashlib
import math
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from app.providers.base import MarketDataProvider
from app.schemas.market_data import (
    EarningsDate,
    OptionChain,
    OptionContract,
    Quote,
)

# ── Realistic spot prices & IV for 5 NASDAQ tickers ──────────────────────
_TICKER_DATA: Dict[str, dict] = {
    "TSLA": {"price": 340.00, "iv_base": 0.55, "earnings": "2025-04-22"},
    "META": {"price": 620.00, "iv_base": 0.38, "earnings": "2025-04-30"},
    "AAPL": {"price": 228.00, "iv_base": 0.25, "earnings": "2025-05-01"},
    "AMZN": {"price": 215.00, "iv_base": 0.35, "earnings": "2025-04-24"},
    "QQQ": {"price": 520.00, "iv_base": 0.22, "earnings": None},  # ETF – no earnings
}


def _seed(symbol: str, strike: float, dte: int) -> float:
    """Deterministic pseudo-random float in [0, 1) from symbol+strike+dte."""
    h = hashlib.md5(f"{symbol}{strike}{dte}".encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


def _bs_delta_approx(spot: float, strike: float, iv: float, dte: int, option_type: str = "call") -> float:
    """
    Quick Black-Scholes-style delta approximation.
    Uses the simplified formula:  delta ≈ N(d1) for calls, N(d1) - 1 for puts.
    """
    if dte <= 0:
        if option_type == "call":
            return 1.0 if spot > strike else 0.0
        else:
            return -1.0 if spot < strike else 0.0
    t = dte / 365.0
    sqrt_t = math.sqrt(t)
    if iv * sqrt_t == 0:
        if option_type == "call":
            return 1.0 if spot > strike else 0.0
        else:
            return -1.0 if spot < strike else 0.0
    d1 = (math.log(spot / strike) + 0.5 * iv * iv * t) / (iv * sqrt_t)
    # Logistic approximation of cumulative normal
    call_delta = 1.0 / (1.0 + math.exp(-1.7 * d1))
    if option_type == "put":
        return call_delta - 1.0  # put delta is negative
    return call_delta


def _bs_gamma_approx(spot: float, strike: float, iv: float, dte: int) -> float:
    """Approximate gamma = N'(d1) / (S * σ * √T)."""
    if dte <= 0 or iv == 0:
        return 0.0
    t = dte / 365.0
    sqrt_t = math.sqrt(t)
    d1 = (math.log(spot / strike) + 0.5 * iv * iv * t) / (iv * sqrt_t)
    n_prime = math.exp(-0.5 * d1 * d1) / math.sqrt(2 * math.pi)
    return n_prime / (spot * iv * sqrt_t)


def _generate_chain(
    symbol: str, spot: float, iv_base: float, as_of: date
) -> List[OptionContract]:
    """Generate realistic option contracts for multiple expiries / strikes."""
    contracts: List[OptionContract] = []

    # Weekly expiries: every Friday for ~6 weeks
    fridays: List[date] = []
    d = as_of + timedelta(days=(4 - as_of.weekday()) % 7 or 7)  # next Friday
    for _ in range(6):
        fridays.append(d)
        d += timedelta(days=7)

    for expiry in fridays:
        dte = (expiry - as_of).days
        if dte < 1:
            continue

        # Strikes: from -10 % to +15 % around spot, rounded to sensible increments
        if spot < 50:
            inc = 1.0
        elif spot < 200:
            inc = 2.5
        elif spot < 500:
            inc = 5.0
        else:
            inc = 10.0

        low = math.floor(spot * 0.90 / inc) * inc
        high = math.ceil(spot * 1.15 / inc) * inc
        strike = low
        while strike <= high:
            gamma = _bs_gamma_approx(spot, strike, iv_base, dte)

            # Theta approximation: theta ≈ -(S * σ * N'(d1)) / (2 * √T)
            t = dte / 365.0
            sqrt_t = math.sqrt(t) if t > 0 else 0.001
            d1 = (
                (math.log(spot / strike) + 0.5 * iv_base**2 * t) / (iv_base * sqrt_t)
                if iv_base * sqrt_t > 0
                else 0
            )
            n_prime_d1 = math.exp(-0.5 * d1**2) / math.sqrt(2 * math.pi)
            theta = -(spot * iv_base * n_prime_d1) / (2 * sqrt_t * 365)

            # Vega approximation: vega = S * N'(d1) * √T / 100
            vega = spot * n_prime_d1 * sqrt_t / 100

            # IV skew: OTM puts have higher IV
            iv = round(iv_base * (1 + 0.1 * (spot - strike) / spot), 4)

            # OI / volume from seed
            noise = _seed(symbol, strike, dte)
            oi = int(200 + 5000 * noise)
            vol = int(20 + 2000 * noise * noise)

            for opt_type in ("call", "put"):
                delta = _bs_delta_approx(spot, strike, iv_base, dte, opt_type)

                # Intrinsic + time value → theoretical mid
                if opt_type == "call":
                    intrinsic = max(spot - strike, 0.0)
                    time_value = spot * iv_base * sqrt_t * 0.4 * max(delta, 0.01)
                else:
                    intrinsic = max(strike - spot, 0.0)
                    time_value = spot * iv_base * sqrt_t * 0.4 * max(abs(delta), 0.01)
                theo_mid = intrinsic + time_value

                # Add noise via seed for bid/ask spread
                spread = max(0.05, theo_mid * (0.03 + 0.04 * noise))
                bid = round(max(0.01, theo_mid - spread / 2), 2)
                ask = round(theo_mid + spread / 2, 2)
                mid_price = round((bid + ask) / 2, 2)
                last = round(mid_price + (noise - 0.5) * spread * 0.3, 2)

                contracts.append(
                    OptionContract(
                        symbol=symbol,
                        expiry=expiry,
                        strike=round(strike, 2),
                        option_type=opt_type,
                        bid=bid,
                        ask=ask,
                        last=last,
                        mid=mid_price,
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
            strike += inc

    return contracts


class MockMarketDataProvider(MarketDataProvider):
    """
    Deterministic mock provider for local development and testing.
    Supports TSLA, META, AAPL, AMZN, QQQ out of the box.
    Unknown symbols get a generic $100 price.
    """

    def get_quote(self, symbol: str) -> Quote:
        sym = symbol.upper()
        data = _TICKER_DATA.get(sym, {"price": 100.00})
        return Quote(
            symbol=sym,
            price=data["price"],
            timestamp=datetime.utcnow(),
        )

    def get_option_chain(
        self, symbol: str, as_of_date: Optional[date] = None
    ) -> OptionChain:
        sym = symbol.upper()
        data = _TICKER_DATA.get(sym, {"price": 100.00, "iv_base": 0.30})
        as_of = as_of_date or date.today()
        contracts = _generate_chain(sym, data["price"], data["iv_base"], as_of)
        return OptionChain(
            symbol=sym,
            as_of=datetime.utcnow(),
            spot=data["price"],
            contracts=contracts,
        )

    def get_earnings_calendar(self, symbol: str) -> EarningsDate:
        sym = symbol.upper()
        data = _TICKER_DATA.get(sym)
        if data and data.get("earnings"):
            return EarningsDate(
                symbol=sym,
                next_earnings=date.fromisoformat(data["earnings"]),
            )
        return EarningsDate(symbol=sym, next_earnings=None)
