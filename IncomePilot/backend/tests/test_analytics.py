"""
Tests for the analytics dashboard endpoint.
Uses the same test DB infrastructure as test_api.py via conftest.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

# Reuse the same test engine pattern — but since test_api.py may also
# override get_db, we use a shared engine setup here.
TEST_ENGINE = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)
TestSession = sessionmaker(bind=TEST_ENGINE)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


client = TestClient(app)


class TestAnalyticsDashboard:
    def test_empty_dashboard(self):
        """Dashboard with no data returns valid structure."""
        r = client.get("/api/analytics/dashboard")
        assert r.status_code == 200
        data = r.json()
        assert "monthly_premiums" in data
        assert "delta_distribution" in data
        assert "pnl" in data
        assert data["monthly_premiums"] == []
        assert data["pnl"]["realized_pnl"] == 0.0

    def test_dashboard_with_trades(self):
        """Dashboard after seeding a trade."""
        trade = {
            "symbol": "AAPL",
            "strategy_type": "CC",
            "trade_type": "fresh",
            "strike": 230.0,
            "expiry": "2025-04-18",
            "premium": 2.50,
            "contracts": 1,
            "trade_date": "2025-03-01",
            "owner": "Venky",
        }
        r = client.post("/api/trades", json=trade)
        assert r.status_code == 201

        r = client.get("/api/analytics/dashboard")
        assert r.status_code == 200
        data = r.json()
        assert len(data["monthly_premiums"]) == 1
        assert data["monthly_premiums"][0]["month"] == "2025-03"
        assert data["monthly_premiums"][0]["total_premium"] == 250.0
        assert data["pnl"]["total_premium_collected"] == 250.0

    def test_dashboard_with_owner_filter(self):
        """Dashboard respects owner filter."""
        trade = {
            "symbol": "TSLA",
            "strategy_type": "CC",
            "trade_type": "fresh",
            "strike": 350.0,
            "expiry": "2025-04-18",
            "premium": 5.00,
            "contracts": 1,
            "trade_date": "2025-03-15",
            "owner": "Venky",
        }
        client.post("/api/trades", json=trade)

        # Filter by Bharg — should have no data
        r = client.get("/api/analytics/dashboard?owner=Bharg")
        assert r.status_code == 200
        data = r.json()
        assert data["monthly_premiums"] == []
        assert data["pnl"]["total_premium_collected"] == 0.0
