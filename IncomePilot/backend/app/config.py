"""
Application configuration loaded from environment / .env file.
"""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────────────────────────────
    database_url: str = "mysql+pymysql://root@127.0.0.1:3306/incomepilot"

    # ── Market-data provider ──────────────────────────────────────────────
    # "mock" ships with the app; swap to "polygon", "tradier", etc. later
    market_data_provider: str = "mock"

    # ── Strategy defaults (overridable per-user via Settings API) ─────────
    target_delta_min: float = 0.15
    target_delta_max: float = 0.30
    preferred_dte_min: int = 7
    preferred_dte_max: int = 21
    min_annualized_yield: float = 8.0  # percent
    max_assignment_probability: float = 35.0  # percent (delta proxy)
    avoid_earnings_before_days: int = 7
    avoid_earnings_after_days: int = 2
    min_open_interest: int = 100
    min_volume: int = 10

    # ── Scoring weights (must sum to 1.0) ─────────────────────────────────
    w_yield: float = 0.35
    w_delta_fit: float = 0.25
    w_liquidity: float = 0.20
    w_distance: float = 0.10
    w_earnings_safety: float = 0.10
    w_theta_efficiency: float = 0.0
    w_spread: float = 0.0

    # ── Roll engine thresholds ────────────────────────────────────────────
    roll_max_debit: float = 0.50  # max debit ($) allowed when rolling
    roll_min_dte_search: int = 7
    roll_max_dte_search: int = 45
    deep_itm_ratio: float = 2.0
    gamma_zone_dte: int = 5

    # ── Market-data constants ─────────────────────────────────────────────
    risk_free_rate: float = 0.045
    dividend_yield: float = 0.0

    # ── Scoring thresholds ─────────────────────────────────────────────
    liquidity_oi_threshold: int = 1000
    liquidity_volume_threshold: int = 500
    distance_peak_otm: float = 0.05
    distance_range: float = 0.10
    spread_min_pct: float = 0.02
    spread_max_pct: float = 0.20

    # ── Provider API keys ────────────────────────────────────────────────
    tradier_api_key: str = ""
    tradier_sandbox: bool = True

    # ── AI / Earnings analysis ───────────────────────────────────────────
    anthropic_api_key: str = ""
    ai_model: str = "claude-sonnet-4-20250514"

    # ── CORS ──────────────────────────────────────────────────────────────
    cors_origins: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
