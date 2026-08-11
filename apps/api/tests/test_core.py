"""API tests — run with: pytest apps/api/tests -q"""
from __future__ import annotations

import os
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

# Force test settings before app import
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-ci")
os.environ.setdefault("CELERY_ALWAYS_EAGER", "true")
os.environ.setdefault("LOG_JSON", "false")


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_live_health():
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/health/live")
        assert res.status_code == 200
        assert res.json()["status"] == "alive"


@pytest.mark.anyio
async def test_root():
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/")
        assert res.status_code == 200
        assert "docs" in res.json()


@pytest.mark.anyio
async def test_entitlements_free_limits():
    from app.core.entitlements import entitlements_for
    from app.db.models import PlanTier

    ents = entitlements_for(PlanTier.free)
    assert ents["property_limit"] == 5
    assert ents["reports"] is False
    assert ents["analyses_per_month"] == 10


@pytest.mark.anyio
async def test_confidence_progress_helpers():
    from app.db.models import PredictionStatus
    from app.modules.predictions.router import _confidence_label, _progress_from_traces

    assert _confidence_label(0.8) == "high"
    assert _confidence_label(0.6) == "medium"
    assert _confidence_label(0.4) == "low"
    prog = _progress_from_traces({"stage": "vision", "stage_message": "Photos"}, PredictionStatus.running)
    assert prog["stage"] == "vision"
    assert 0 < prog["percent"] < 100


@pytest.mark.anyio
async def test_openapi_has_core_paths():
    from app.main import app

    paths = app.openapi()["paths"]
    assert "/v1/auth/register" in paths
    assert "/v1/properties/{property_id}/analyze" in paths
    assert "/v1/billing/usage" in paths
    assert "/health/live" in paths


def test_parse_usd_and_type():
    from app.modules.market.sources import parse_usd_price, property_type_from_title

    assert parse_usd_price("$1,234 for 2 nights") == 1234.0
    assert property_type_from_title("Apartment in Brooklyn") == "apartment"
