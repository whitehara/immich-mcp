import pytest
from immich_mcp.tools import assets
from .conftest import get_annotations, get_fn


@pytest.fixture
def registered(mcp, patch_client):
    assets.register(mcp)
    return mcp, patch_client


# --- immich.assets.list ---

@pytest.mark.asyncio
async def test_list_default_params(registered):
    mcp, client = registered
    client.get.return_value = []

    await get_fn(mcp, "immich.assets.list")()

    client.get.assert_called_once_with("/api/assets", params={"page": 1, "pageSize": 50})


@pytest.mark.asyncio
async def test_list_with_filters(registered):
    mcp, client = registered
    client.get.return_value = []

    await get_fn(mcp, "immich.assets.list")(
        is_favorite=True, is_archived=False, type="IMAGE", page=2, page_size=10
    )

    _, kwargs = client.get.call_args
    assert kwargs["params"]["isFavorite"] is True
    assert kwargs["params"]["isArchived"] is False
    assert kwargs["params"]["type"] == "IMAGE"
    assert kwargs["params"]["page"] == 2


def test_list_is_readonly(registered):
    mcp, _ = registered
    ann = get_annotations(mcp, "immich.assets.list")
    assert ann.readOnlyHint is True
    assert ann.idempotentHint is True


# --- immich.assets.get ---

@pytest.mark.asyncio
async def test_get_calls_correct_endpoint(registered):
    mcp, client = registered
    client.get.return_value = {"id": "abc123", "type": "IMAGE"}

    result = await get_fn(mcp, "immich.assets.get")("abc123")

    client.get.assert_called_once_with("/api/assets/abc123")
    assert result["id"] == "abc123"


def test_get_is_readonly(registered):
    mcp, _ = registered
    ann = get_annotations(mcp, "immich.assets.get")
    assert ann.readOnlyHint is True


# --- immich.assets.update ---

@pytest.mark.asyncio
async def test_update_only_sends_provided_fields(registered):
    mcp, client = registered
    client.put.return_value = {"id": "abc", "isFavorite": True}

    await get_fn(mcp, "immich.assets.update")("abc", is_favorite=True)

    _, kwargs = client.put.call_args
    assert kwargs["json"] == {"isFavorite": True}
    assert "isArchived" not in kwargs["json"]


@pytest.mark.asyncio
async def test_update_all_fields(registered):
    mcp, client = registered
    client.put.return_value = {}

    await get_fn(mcp, "immich.assets.update")(
        "abc", is_favorite=False, is_archived=True, description="test", rating=4
    )

    _, kwargs = client.put.call_args
    assert kwargs["json"] == {
        "isFavorite": False,
        "isArchived": True,
        "description": "test",
        "rating": 4,
    }


def test_update_is_idempotent_not_readonly(registered):
    mcp, _ = registered
    ann = get_annotations(mcp, "immich.assets.update")
    assert ann.readOnlyHint is None or ann.readOnlyHint is False
    assert ann.idempotentHint is True


# --- immich.assets.bulk_update ---

@pytest.mark.asyncio
async def test_bulk_update_dry_run_returns_preview(registered):
    mcp, client = registered

    result = await get_fn(mcp, "immich.assets.bulk_update")(
        ["id1", "id2"], is_favorite=True, dry_run=True
    )

    client.put.assert_not_called()
    assert result["dry_run"] is True
    assert result["affected_count"] == 2
    assert result["changes"]["isFavorite"] is True


@pytest.mark.asyncio
async def test_bulk_update_executes_when_not_dry_run(registered):
    mcp, client = registered
    client.put.return_value = {}

    await get_fn(mcp, "immich.assets.bulk_update")(
        ["id1", "id2"], is_favorite=True, dry_run=False
    )

    client.put.assert_called_once()
    _, kwargs = client.put.call_args
    assert kwargs["json"]["ids"] == ["id1", "id2"]
    assert kwargs["json"]["isFavorite"] is True


# --- immich.assets.delete ---

@pytest.mark.asyncio
async def test_delete_dry_run_default_no_api_call(registered):
    mcp, client = registered

    result = await get_fn(mcp, "immich.assets.delete")(["id1", "id2"])

    client.delete.assert_not_called()
    assert result["dry_run"] is True
    assert result["affected_count"] == 2
    assert result["permanent"] is False


@pytest.mark.asyncio
async def test_delete_executes_with_dry_run_false(registered):
    mcp, client = registered

    result = await get_fn(mcp, "immich.assets.delete")(["id1"], dry_run=False)

    client.delete.assert_called_once_with(
        "/api/assets", json={"ids": ["id1"], "force": False}
    )
    assert result["deleted"] == 1


@pytest.mark.asyncio
async def test_delete_force_permanent(registered):
    mcp, client = registered

    await get_fn(mcp, "immich.assets.delete")(["id1"], force=True, dry_run=False)

    _, kwargs = client.delete.call_args
    assert kwargs["json"]["force"] is True


def test_delete_is_destructive(registered):
    mcp, _ = registered
    ann = get_annotations(mcp, "immich.assets.delete")
    assert ann.destructiveHint is True
    assert ann.idempotentHint is True


# --- immich.assets.statistics ---

@pytest.mark.asyncio
async def test_statistics_calls_endpoint(registered):
    mcp, client = registered
    client.get.return_value = {"images": 1000, "videos": 50, "total": 1050}

    result = await get_fn(mcp, "immich.assets.statistics")()

    client.get.assert_called_once_with("/api/assets/statistics")
    assert result["total"] == 1050


def test_statistics_is_readonly(registered):
    mcp, _ = registered
    ann = get_annotations(mcp, "immich.assets.statistics")
    assert ann.readOnlyHint is True


# --- web_url in responses ---

@pytest.mark.asyncio
async def test_get_includes_web_url(registered):
    mcp, client = registered
    client.get.return_value = {"id": "abc123", "type": "IMAGE"}

    result = await get_fn(mcp, "immich.assets.get")("abc123")

    assert "web_url" in result
    assert "abc123" in result["web_url"]


@pytest.mark.asyncio
async def test_list_includes_web_url_per_asset(registered):
    mcp, client = registered
    client.get.return_value = [{"id": "a1"}, {"id": "a2"}]

    result = await get_fn(mcp, "immich.assets.list")()

    assert all("web_url" in a for a in result)
    assert "a1" in result[0]["web_url"]


# --- immich.assets.view ---

@pytest.mark.asyncio
async def test_view_returns_urls(registered):
    mcp, _ = registered

    result = await get_fn(mcp, "immich.assets.view")("asset-xyz")

    assert result["asset_id"] == "asset-xyz"
    assert "asset-xyz" in result["thumbnail_url"]
    assert "asset-xyz" in result["original_url"]
    assert "asset-xyz" in result["web_url"]
    assert "apiKey=" in result["thumbnail_url"]
    assert "apiKey=" in result["original_url"]


def test_view_is_readonly(registered):
    mcp, _ = registered
    ann = get_annotations(mcp, "immich.assets.view")
    assert ann.readOnlyHint is True
    assert ann.idempotentHint is True


# --- immich.assets.upload ---

@pytest.mark.asyncio
async def test_upload_from_file_path(registered, tmp_path):
    mcp, client = registered
    client.post.return_value = {"id": "new-asset", "status": "created"}

    test_file = tmp_path / "photo.jpg"
    test_file.write_bytes(b"\xff\xd8\xff\xe0fake jpeg")

    result = await get_fn(mcp, "immich.assets.upload")(str(test_file))

    client.post.assert_called_once()
    _, kwargs = client.post.call_args
    assert kwargs["files"]["assetData"][0] == "photo.jpg"
    assert kwargs["data"]["deviceId"] == "immich-mcp"
    assert result["id"] == "new-asset"
    assert "web_url" in result


@pytest.mark.asyncio
async def test_upload_from_url(registered):
    from unittest.mock import AsyncMock, MagicMock, patch

    mcp, client = registered
    client.post.return_value = {"id": "url-asset", "status": "created"}

    mock_response = MagicMock()
    mock_response.content = b"fake image data"
    mock_response.headers = {"content-type": "image/jpeg"}
    mock_response.raise_for_status = MagicMock()

    mock_http = AsyncMock()
    mock_http.get = AsyncMock(return_value=mock_response)
    mock_http.__aenter__ = AsyncMock(return_value=mock_http)
    mock_http.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=mock_http):
        result = await get_fn(mcp, "immich.assets.upload")(
            "https://example.com/photo.jpg"
        )

    client.post.assert_called_once()
    _, kwargs = client.post.call_args
    assert kwargs["files"]["assetData"][0] == "photo.jpg"
    assert result["id"] == "url-asset"
    assert "web_url" in result


@pytest.mark.asyncio
async def test_upload_custom_device_asset_id(registered, tmp_path):
    mcp, client = registered
    client.post.return_value = {"id": "x"}

    f = tmp_path / "img.png"
    f.write_bytes(b"data")

    await get_fn(mcp, "immich.assets.upload")(
        str(f), device_asset_id="my-device-id-123"
    )

    _, kwargs = client.post.call_args
    assert kwargs["data"]["deviceAssetId"] == "my-device-id-123"
