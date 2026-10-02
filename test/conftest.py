"""Pytest fixtures and env setup for kite x402 tests."""

import os

import pytest

# Set env before importing server (pytest collects conftest first on py39+).
os.environ.setdefault("PAY_TO", "0x0000000000000000000000000000000000000000")
os.environ.setdefault("UPSTREAM_URL", "https://api.open-meteo.com")
os.environ.setdefault("KITE_NETWORK", "testnet")
os.environ.setdefault("PRICE_USD", "0.001")


@pytest.fixture
def fresh_env(monkeypatch):
    """Fixture isolating env vars for tests that need custom env."""
    return monkeypatch
