import pytest
from immich_mcp.tools import shared_links
from .conftest import get_annotations, get_fn


@pytest.fixture
def registered(mcp, patch_client):
    shared_links.register(mcp)
    return mcp, patch_client


@pytest.mark.asyncio
async def test_list_shared_links(registered):
    mcp, client = registered
    client.get.return_value = [{"id": "sl1", "type": "ALBUM"}]

    result = await get_fn(mcp, "immich_shared_links_list")()

    client.get.assert_called_once_with("/api/shared-links")
    assert result[0]["id"] == "sl1"


@pytest.mark.asyncio
async def test_get_shared_link(registered):
    mcp, client = registered
    client.get.return_value = {"id": "sl1"}

    await get_fn(mcp, "immich_shared_links_get")("sl1")

    client.get.assert_called_once_with("/api/shared-links/sl1")


@pytest.mark.asyncio
async def test_create_album_link(registered):
    mcp, client = registered
    client.post.return_value = {"id": "sl-new", "link": "https://..."}

    await get_fn(mcp, "immich_shared_links_create")("ALBUM", album_id="a1")

    _, kwargs = client.post.call_args
    assert kwargs["json"]["type"] == "ALBUM"
    assert kwargs["json"]["albumId"] == "a1"
    assert kwargs["json"]["allowDownload"] is True
    assert kwargs["json"]["allowUpload"] is False


@pytest.mark.asyncio
async def test_create_asset_link_with_password(registered):
    mcp, client = registered
    client.post.return_value = {}

    await get_fn(mcp, "immich_shared_links_create")(
        "INDIVIDUAL", asset_ids=["id1"], password="secret", expires_at="2025-01-01T00:00:00Z"
    )

    _, kwargs = client.post.call_args
    assert kwargs["json"]["assetIds"] == ["id1"]
    assert kwargs["json"]["password"] == "secret"
    assert kwargs["json"]["expiresAt"] == "2025-01-01T00:00:00Z"


@pytest.mark.asyncio
async def test_update_shared_link(registered):
    mcp, client = registered
    client.patch.return_value = {}

    await get_fn(mcp, "immich_shared_links_update")("sl1", allow_download=False)

    client.patch.assert_called_once_with(
        "/api/shared-links/sl1", json={"allowDownload": False}
    )


@pytest.mark.asyncio
async def test_remove_shared_link(registered):
    mcp, client = registered

    result = await get_fn(mcp, "immich_shared_links_remove")("sl1")

    client.delete.assert_called_once_with("/api/shared-links/sl1")
    assert result["removed"] == "sl1"


def test_remove_is_destructive(registered):
    mcp, _ = registered
    ann = get_annotations(mcp, "immich_shared_links_remove")
    assert ann.destructiveHint is True


def test_list_is_readonly(registered):
    mcp, _ = registered
    ann = get_annotations(mcp, "immich_shared_links_list")
    assert ann.readOnlyHint is True
