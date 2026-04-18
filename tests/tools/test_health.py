import pytest
from immich_mcp.tools import health
from .conftest import get_annotations, get_fn


@pytest.fixture
def registered(mcp, patch_client):
    health.register(mcp)
    return mcp, patch_client


@pytest.mark.asyncio
async def test_ping_calls_about_endpoint(registered):
    mcp, client = registered
    client.get.return_value = {"version": "1.100.0", "nodejs": "20.0.0"}

    result = await get_fn(mcp, "immich_ping")()

    client.get.assert_called_once_with("/api/server/about")
    assert result["version"] == "1.100.0"


@pytest.mark.asyncio
async def test_capabilities_calls_features_endpoint(registered):
    mcp, client = registered
    client.get.return_value = {"smartSearch": True, "duplicateDetection": True}

    result = await get_fn(mcp, "immich_capabilities")()

    client.get.assert_called_once_with("/api/server/features")
    assert result["duplicateDetection"] is True


def test_ping_is_readonly(registered):
    mcp, _ = registered
    ann = get_annotations(mcp, "immich_ping")
    assert ann.readOnlyHint is True
    assert ann.idempotentHint is True


def test_capabilities_is_readonly(registered):
    mcp, _ = registered
    ann = get_annotations(mcp, "immich_capabilities")
    assert ann.readOnlyHint is True
    assert ann.idempotentHint is True
