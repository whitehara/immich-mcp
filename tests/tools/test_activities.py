import pytest
from immich_mcp.tools import activities
from .conftest import get_annotations, get_fn


@pytest.fixture
def registered(mcp, patch_client):
    activities.register(mcp)
    return mcp, patch_client


@pytest.mark.asyncio
async def test_list_activities_album_only(registered):
    mcp, client = registered
    client.get.return_value = []

    await get_fn(mcp, "immich.activities.list")("album-1")

    client.get.assert_called_once_with(
        "/api/activities", params={"albumId": "album-1"}
    )


@pytest.mark.asyncio
async def test_list_activities_with_asset_filter(registered):
    mcp, client = registered
    client.get.return_value = []

    await get_fn(mcp, "immich.activities.list")("album-1", asset_id="asset-1")

    _, kwargs = client.get.call_args
    assert kwargs["params"]["assetId"] == "asset-1"


@pytest.mark.asyncio
async def test_create_comment(registered):
    mcp, client = registered
    client.post.return_value = {"id": "act-1", "type": "comment"}

    result = await get_fn(mcp, "immich.activities.create")(
        "album-1", "comment", comment="Great photo!"
    )

    _, kwargs = client.post.call_args
    assert kwargs["json"]["albumId"] == "album-1"
    assert kwargs["json"]["type"] == "comment"
    assert kwargs["json"]["comment"] == "Great photo!"


@pytest.mark.asyncio
async def test_create_like(registered):
    mcp, client = registered
    client.post.return_value = {}

    await get_fn(mcp, "immich.activities.create")(
        "album-1", "like", asset_id="asset-1"
    )

    _, kwargs = client.post.call_args
    assert kwargs["json"]["type"] == "like"
    assert kwargs["json"]["assetId"] == "asset-1"
    assert "comment" not in kwargs["json"]


@pytest.mark.asyncio
async def test_delete_activity(registered):
    mcp, client = registered

    result = await get_fn(mcp, "immich.activities.delete")("act-1")

    client.delete.assert_called_once_with("/api/activities/act-1")
    assert result["deleted"] == "act-1"


@pytest.mark.asyncio
async def test_statistics(registered):
    mcp, client = registered
    client.get.return_value = {"comments": 5}

    result = await get_fn(mcp, "immich.activities.statistics")("album-1")

    client.get.assert_called_once_with(
        "/api/activities/statistics", params={"albumId": "album-1"}
    )
    assert result["comments"] == 5


def test_delete_is_destructive(registered):
    mcp, _ = registered
    ann = get_annotations(mcp, "immich.activities.delete")
    assert ann.destructiveHint is True


def test_list_is_readonly(registered):
    mcp, _ = registered
    ann = get_annotations(mcp, "immich.activities.list")
    assert ann.readOnlyHint is True
    assert ann.idempotentHint is True
