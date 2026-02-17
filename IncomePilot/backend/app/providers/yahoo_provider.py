"""
Yahoo Finance market-data provider using the yfinance library.

Usage:
  1. pip install yfinance
  2. Set MARKET_DATA_PROVIDER=yahoo in .env
"""

from __future__ import annotations

import logging
import math
from datetime import date, datetime
from typing import Optional

import yfinance as yf

from app.providers.base import MarketDataProvider
from app.schemas.market_data import (
    EarningsDate,
    OptionChain,
    OptionContract,
    Quote,
)

logger = logging.getLogger(__name__)

# US 10-year treasury proxy — update periodically or fetch dynamically
_RISK_FREE_RATE = 0.045


# ── NaN-safe helpers ──────────────────────────────────────────────────────


def _safe_float(val, default: float = 0.0) -> float:
    try:
        if val is None or (isinstance(val, float) and math.isnan(val)):
            return default
        return float(val)
    except (ValueError, TypeError):
        return default


def _safe_int(val) -> int:
    try:
        if val is None or (isinstance(val, float) and math.isnan(val)):
            return 0
        return int(val)
    except (ValueError, TypeError):
        return 0


# ── Black-Scholes Greeks ─────────────────────────────────────────────────
#
# Full BS model for European call:
#   d1 = [ln(S/K) + (r + σ²/2) * T] / (σ * √T)
#   d2 = d1 - σ * √T
#   delta = e^(-q*T) * N(d1)     (q = dividend yield, assumed 0 here)
#   gamma = e^(-q*T) * n(d1) / (S * σ * √T)
#   theta = [-S * e^(-q*T) * n(d1) * σ / (2√T)
#            - r * K * e^(-r*T) * N(d2)] / 365
#
# where N() = standard normal CDF, n() = standard normal PDF


def _norm_cdf(x: float) -> float:
    """Standard normal cumulative distribution function."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _norm_pdf(x: float) -> float:
    """Standard normal probability density function."""
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def _bs_d1(S: float, K: float, T: float, sigma: float, r: float) -> float:
    """Black-Scholes d1."""
    return (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))


def _bs_d2(d1: float, sigma: float, T: float) -> float:
    """Black-Scholes d2."""
    return d1 - sigma * math.sqrt(T)


def _bs_delta(S: float, K: float, T: float, sigma: float, r: float) -> float:
    """Call delta = N(d1). Range [0, 1]."""
    if sigma <= 0 or T <= 0 or S <= 0 or K <= 0:
        return 1.0 if S > K else 0.0
    d1 = _bs_d1(S, K, T, sigma, r)
    return round(_norm_cdf(d1), 4)


def _bs_gamma(S: float, K: float, T: float, sigma: float, r: float) -> float:
    """Call gamma = n(d1) / (S * σ * √T)."""
    if sigma <= 0 or T <= 0 or S <= 0 or K <= 0:
        return 0.0
    d1 = _bs_d1(S, K, T, sigma, r)
    return round(_norm_pdf(d1) / (S * sigma * math.sqrt(T)), 6)


def _bs_theta(S: float, K: float, T: float, sigma: float, r: float) -> float:
    """
    Call theta (per day).
    θ = [-S * n(d1) * σ / (2√T) - r * K * e^(-rT) * N(d2)] / 365
    """
    if sigma <= 0 or T <= 0 or S <= 0 or K <= 0:
        return 0.0
    d1 = _bs_d1(S, K, T, sigma, r)
    d2 = _bs_d2(d1, sigma, T)
    term1 = -S * _norm_pdf(d1) * sigma / (2.0 * math.sqrt(T))
    term2 = -r * K * math.exp(-r * T) * _norm_cdf(d2)
    return round((term1 + term2) / 365.0, 4)


def _implied_vol_from_price(
    S: float, K: float, T: float, market_price: float, r: float
) -> float:
    """
    Newton-Raphson solver for implied volatility from a call price.
    Used as fallback when Yahoo returns IV=0 but we have a valid mid price.
    """
    if market_price <= 0 or S <= 0 or K <= 0 or T <= 0:
        return 0.0

    # Intrinsic value floor
    intrinsic = max(S * math.exp(-r * T) - K * math.exp(-r * T), 0)
    if market_price <= intrinsic:
        return 0.05  # minimum floor

    # Initial guess from Brenner-Subrahmanyam approximation
    sigma = math.sqrt(2.0 * math.pi / T) * (market_price / S)
    sigma = max(0.05, min(sigma, 5.0))

    for _ in range(50):
        try:
            d1 = _bs_d1(S, K, T, sigma, r)
            d2 = _bs_d2(d1, sigma, T)
            bs_price = S * _norm_cdf(d1) - K * math.exp(-r * T) * _norm_cdf(d2)
            vega = S * _norm_pdf(d1) * math.sqrt(T)
            if vega < 1e-10:
                break
            diff = bs_price - market_price
            if abs(diff) < 1e-6:
                break
            sigma -= diff / vega
            sigma = max(0.01, min(sigma, 10.0))
        except (ValueError, ZeroDivisionError):
            break

    return max(0.01, min(sigma, 10.0))


# ── Provider ──────────────────────────────────────────────────────────────


class YahooFinanceProvider(MarketDataProvider):
    """Fetches live market data from Yahoo Finance (free, no API key)."""

    # ── Quote ──────────────────────────────────────────────────────────────

    def get_quote(self, symbol: str) -> Quote:
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info
        price = float(info.last_price)
        return Quote(symbol=symbol.upper(), price=price, timestamp=datetime.utcnow())

    # ── Option chain ──────────────────────────────────────────────────────

    def get_option_chain(
        self, symbol: str, as_of_date: Optional[date] = None
    ) -> OptionChain:
        ticker = yf.Ticker(symbol)
        spot = float(ticker.fast_info.last_price)
        today = as_of_date or date.today()
        r = _RISK_FREE_RATE

        expirations = ticker.options  # list of "YYYY-MM-DD" strings
        if not expirations:
            return OptionChain(
                symbol=symbol.upper(),
                as_of=datetime.utcnow(),
                spot=spot,
                contracts=[],
            )

        contracts: list[OptionContract] = []
        for exp_str in expirations:
            exp_date = date.fromisoformat(exp_str)
            dte = (exp_date - today).days
            if dte < 1 or dte > 60:
                continue

            try:
                chain = ticker.option_chain(exp_str)
            except Exception:
                logger.warning("Failed to fetch chain for %s exp %s", symbol, exp_str)
                continue

            T = dte / 365.0  # time to expiry in years

            for opt_type, df in [("call", chain.calls), ("put", chain.puts)]:
                for _, row in df.iterrows():
                    strike = _safe_float(row.get("strike"))
                    if strike <= 0:
                        continue

                    bid = _safe_float(row.get("bid"))
                    ask = _safe_float(row.get("ask"))
                    last = _safe_float(row.get("lastPrice"))
                    mid = round((bid + ask) / 2, 2) if (bid + ask) > 0 else last
                    iv = _safe_float(row.get("impliedVolatility"))
                    oi = _safe_int(row.get("openInterest"))
                    vol = _safe_int(row.get("volume"))

                    # ── Resolve IV ─────────────────────────────────────────
                    stale_data = bid <= 0 and ask <= 0
                    price_for_iv = last if stale_data else mid

                    if stale_data and price_for_iv > 0:
                        iv = round(
                            _implied_vol_from_price(spot, strike, T, price_for_iv, r), 4
                        )
                    elif iv < 0.05 and price_for_iv > 0:
                        iv = round(
                            _implied_vol_from_price(spot, strike, T, price_for_iv, r), 4
                        )

                    # ── Compute Greeks from Black-Scholes ──────────────────
                    if opt_type == "call":
                        delta = _bs_delta(spot, strike, T, iv, r)
                    else:
                        # Put delta = call delta - 1
                        delta = round(_bs_delta(spot, strike, T, iv, r) - 1.0, 4)
                    gamma = _bs_gamma(spot, strike, T, iv, r)
                    theta = _bs_theta(spot, strike, T, iv, r)

                    contracts.append(
                        OptionContract(
                            symbol=symbol.upper(),
                            expiry=exp_date,
                            strike=strike,
                            option_type=opt_type,
                            bid=bid,
                            ask=ask,
                            last=last,
                            mid=mid,
                            iv=round(iv, 4),
                            delta=delta,
                            gamma=gamma,
                            theta=theta,
                            open_interest=oi,
                            volume=vol,
                            dte=dte,
                        )
                    )

        return OptionChain(
            symbol=symbol.upper(),
            as_of=datetime.utcnow(),
            spot=spot,
            contracts=contracts,
        )

    # ── Earnings calendar ─────────────────────────────────────────────────

    def get_earnings_calendar(self, symbol: str) -> EarningsDate:
        ticker = yf.Ticker(symbol)
        try:
            cal = ticker.calendar
            if cal is not None and isinstance(cal, dict):
                earnings_date = cal.get("Earnings Date")
                if earnings_date:
                    # Can be a list of dates or a single Timestamp
                    if isinstance(earnings_date, list) and len(earnings_date) > 0:
                        ed = earnings_date[0]
                    else:
                        ed = earnings_date
                    if hasattr(ed, "date"):
                        return EarningsDate(
                            symbol=symbol.upper(), next_earnings=ed.date()
                        )
                    elif isinstance(ed, str):
                        return EarningsDate(
                            symbol=symbol.upper(),
                            next_earnings=date.fromisoformat(ed),
                        )
        except Exception:
            logger.warning("Could not fetch earnings for %s", symbol)

        return EarningsDate(symbol=symbol.upper(), next_earnings=None)
