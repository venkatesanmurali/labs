"""
API integration tests using FastAPI's TestClient.
Uses an in-memory SQLite database to avoid requiring MySQL for CI.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

# Use SQLite in-memory for tests (no MySQL needed).
# StaticPool + check_same_thread=False ensures the same connection is reused
# across the main thread and the ASGI server thread.
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


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


client = TestClient(app)


class TestHealthEndpoint:
    def test_health(self):
        r = client.get("/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


class TestHoldingsAPI:
    def test_create_and_list(self):
        payload = {
            "symbol": "AAPL",
            "shares": 100,
            "avg_cost": 150.0,
            "account_type": "taxable",
        }
        r = client.post("/api/holdings", json=payload)
        assert r.status_code == 201
        data = r.json()
        assert data["symbol"] == "AAPL"
        assert data["id"] > 0

        r2 = client.get("/api/holdings")
        assert r2.status_code == 200
        assert len(r2.json()) == 1

    def test_update_holding(self):
        r = client.post(
            "/api/holdings",
            json={"symbol": "TSLA", "shares": 50, "avg_cost": 200.0, "account_type": "taxable"},
        )
        hid = r.json()["id"]
        r2 = client.put(f"/api/holdings/{hid}", json={"shares": 100})
        assert r2.status_code == 200
        assert r2.json()["shares"] == 100

    def test_delete_holding(self):
        r = client.post(
            "/api/holdings",
            json={"symbol": "QQQ", "shares": 200, "avg_cost": 400.0, "account_type": "retirement"},
        )
        hid = r.json()["id"]
        r2 = client.delete(f"/api/holdings/{hid}")
        assert r2.status_code == 204

    def test_demo_load(self):
        r = client.post("/api/holdings/demo")
        assert r.status_code == 200
        assert len(r.json()) == 3


class TestRecommendationsAPI:
    def test_get_recommendations(self):
        r = client.get("/api/recommendations/AAPL")
        assert r.status_code == 200
        data = r.json()
        assert data["symbol"] == "AAPL"
        assert "candidates" in data


class TestSettingsAPI:
    def test_get_default_settings(self):
        r = client.get("/api/settings")
        assert r.status_code == 200
        data = r.json()
        assert data["target_delta_min"] == 0.15

    def test_update_settings(self):
        r = client.put("/api/settings", json={"target_delta_min": 0.10})
        assert r.status_code == 200
        assert r.json()["target_delta_min"] == 0.10
