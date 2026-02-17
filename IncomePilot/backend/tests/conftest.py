"""Shared test fixtures."""

from __future__ import annotations

import pytest

from app.providers.mock_provider import MockMarketDataProvider


@pytest.fixture
def mock_provider() -> MockMarketDataProvider:
    return MockMarketDataProvider()
