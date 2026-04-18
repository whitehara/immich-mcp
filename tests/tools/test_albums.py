import pytest
from immich_mcp.tools import albums
from .conftest import get_annotations, get_fn


@pytest.fixture
def registered(mcp, patch_client):
    albums.register(mcp)
    return mcp, patch_client


@pytest.mark.asyncio
async def test_list_all_albums(registered):
    mcp, client = registered
    client.get.return_value = [{"id": "a1", "albumName": "Vacation"}]

    result = await get_fn(mcp, "immich.albums.list")()

    client.get.assert_called_once_with("/api/albums", params={})
    assert len(result) == 1


@pytest.mark.asyncio
async def test_list_shared_filter(registered):
    mcp, client = registered
    client.get.return_value = []

    await get_fn(mcp, "immich.albums.list")(shared=True)

    _, kwargs = client.get.call_args
    assert kwargs["params"]["shared"] is True


@pytest.mark.asyncio
async def test_get_album(registered):
    mcp, client = registered
    client.get.return_value = {"id": "a1", "assets": []}

    result = await get_fn(mcp, "immich.albums.get")("a1")

    client.get.assert_called_once_with("/api/albums/a1", params={"withoutAssets": False})
    assert result["id"] == "a1"


@pytest.mark.asyncio
async def test_create_album_minimal(registered):
    mcp, client = registered
    client.post.return_value = {"id": "new-album", "albumName": "Trip"}

    result = await get_fn(mcp, "immich.albums.create")("Trip")

    _, kwargs = client.post.call_args
    assert kwargs["json"] == {"albumName": "Trip"}
    assert result["albumName"] == "Trip"


@pytest.mark.asyncio
async def test_create_album_with_assets(registered):
    mcp, client = registered
    client.post.return_value = {}

    await get_fn(mcp, "immich.albums.create")(
        "Trip", description="2024 Tokyo trip", asset_ids=["id1", "id2"]
    )

    _, kwargs = client.post.call_args
    assert kwargs["json"]["description"] == "2024 Tokyo trip"
    assert kwargs["json"]["assetIds"] == ["id1", "id2"]


@pytest.mark.asyncio
async def test_update_album(registered):
    mcp, client = registered
    client.patch.return_value = {}

    await get_fn(mcp, "immich.albums.update")("a1", album_name="New Name")

    client.patch.assert_called_once_with(
        "/api/albums/a1", json={"albumName": "New Name"}
    )


@pytest.mark.asyncio
async def test_delete_album(registered):
    mcp, client = registered

    result = await get_fn(mcp, "immich.albums.delete")("a1")

    client.delete.assert_called_once_with("/api/albums/a1")
    assert result["deleted"] == "a1"


def test_delete_is_destructive(registered):
    mcp, _ = registered
    ann = get_annotations(mcp, "immich.albums.delete")
    assert ann.destructiveHint is True


@pytest.mark.asyncio
async def test_add_assets(registered):
    mcp, client = registered
    client.put.return_value = {"successfullyAdded": 2}

    await get_fn(mcp, "immich.albums.add_assets")("a1", ["id1", "id2"])

    client.put.assert_called_once_with(
        "/api/albums/a1/assets", json={"ids": ["id1", "id2"]}
    )


@pytest.mark.asyncio
async def test_remove_assets(registered):
    mcp, client = registered
    client.delete.return_value = {"removed": 1}

    await get_fn(mcp, "immich.albums.remove_assets")("a1", ["id1"])

    client.delete.assert_called_once_with(
        "/api/albums/a1/assets", json={"ids": ["id1"]}
    )


# --- web_url in album responses ---

@pytest.mark.asyncio
async def test_list_adds_web_url(registered):
    mcp, client = registered
    client.get.return_value = [{"id": "alb-1"}, {"id": "alb-2"}]

    result = await get_fn(mcp, "immich.albums.list")()

    assert all("web_url" in a for a in result)
    assert "alb-1" in result[0]["web_url"]


@pytest.mark.asyncio
async def test_get_adds_web_url_to_album_and_assets(registered):
    mcp, client = registered
    client.get.return_value = {
        "id": "alb-1",
        "assets": [{"id": "asset-1"}, {"id": "asset-2"}],
    }

    result = await get_fn(mcp, "immich.albums.get")("alb-1")

    assert "web_url" in result
    assert "alb-1" in result["web_url"]
    assert all("web_url" in a for a in result["assets"])


@pytest.mark.asyncio
async def test_create_adds_web_url(registered):
    mcp, client = registered
    client.post.return_value = {"id": "new-alb", "albumName": "Trip"}

    result = await get_fn(mcp, "immich.albums.create")("Trip")

    assert "web_url" in result
    assert "new-alb" in result["web_url"]
