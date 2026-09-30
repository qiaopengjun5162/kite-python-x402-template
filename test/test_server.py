"""Tests for server.py — FastAPI application and 402 middleware (extended)."""

import sys

sys.path.insert(0, ".")

import os

import pytest
from httpx import ASGITransport, AsyncClient

# Set env before importing app
os.environ["PAY_TO"] = "0x0000000000000000000000000000000000000000"
os.environ["UPSTREAM_URL"] = "https://api.open-meteo.com"
os.environ["KITE_NETWORK"] = "testnet"
os.environ["PRICE_USD"] = "0.001"

from server import (
    CHAIN,
    PAY_TO,
    PRICE,
    UPSTREAM_AUTH_HEADER,
    UPSTREAM_AUTH_VALUE,
    UPSTREAM_URL,
    app,
)


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---- Health check ----


@pytest.mark.asyncio
async def test_healthz(client):
    resp = await client.get("/healthz")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["network"] == "eip155:2368"
    assert data["asset"] == "pieUSD"
    assert data["price"] == "$0.001"


# ---- 402 responses for unpaid requests ----


@pytest.mark.asyncio
async def test_v1_unpaid_returns_402(client):
    resp = await client.get("/v1/forecast?latitude=52.52&longitude=13.41")
    assert resp.status_code == 402
    assert "payment-required" in resp.headers
    assert resp.headers.get("cache-control") == "no-store"


@pytest.mark.asyncio
async def test_v1_wildcard_returns_402(client):
    resp = await client.get("/v1/some/other/path")
    assert resp.status_code == 402


@pytest.mark.asyncio
async def test_v1_post_returns_402(client):
    resp = await client.post("/v1/data", json={"key": "value"})
    assert resp.status_code == 402


@pytest.mark.asyncio
async def test_v1_put_returns_402(client):
    resp = await client.put("/v1/resource/1", json={"name": "test"})
    assert resp.status_code == 402


@pytest.mark.asyncio
async def test_v1_delete_returns_402(client):
    resp = await client.delete("/v1/resource/1")
    assert resp.status_code == 402


# ---- Payment header shape ----


@pytest.mark.asyncio
async def test_payment_header_is_base64_json(client):
    resp = await client.get("/v1/forecast?latitude=52.52&longitude=13.41")
    import base64
    import json

    raw = resp.headers["payment-required"]
    decoded = base64.b64decode(raw)
    body = json.loads(decoded)
    assert body["x402Version"] == 2
    assert body["error"] == "Payment required"
    assert len(body["accepts"]) > 0
    offer = body["accepts"][0]
    assert offer["scheme"] == "exact"
    assert offer["network"] == "eip155:2368"
    assert "amount" in offer
    assert "payTo" in offer
    assert "asset" in offer
    assert "maxTimeoutSeconds" in offer


# ---- Non-402 paths should be free ----


@pytest.mark.asyncio
async def test_healthz_is_free(client):
    resp = await client.get("/healthz")
    assert resp.status_code == 200
    assert "payment-required" not in resp.headers


@pytest.mark.asyncio
async def test_root_is_free(client):
    resp = await client.get("/")
    # FastAPI returns 404 for unknown routes, not 402
    assert resp.status_code != 402
    assert "payment-required" not in resp.headers


@pytest.mark.asyncio
async def test_openapi_docs_is_free(client):
    resp = await client.get("/docs")
    assert resp.status_code in (200, 302)  # redirect or ok


# ---- Env/config validation ----


def test_env_vars_loaded():
    """Verify that the module-scoped env vars parsed correctly."""
    assert PAY_TO == "0x0000000000000000000000000000000000000000"
    assert UPSTREAM_URL == "https://api.open-meteo.com"
    assert CHAIN.asset_symbol == "pieUSD"
    assert PRICE == "$0.001"
    assert UPSTREAM_AUTH_HEADER == "Authorization"
    assert UPSTREAM_AUTH_VALUE == ""
