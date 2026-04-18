import pytest
from immich_mcp.tools import tags
from .conftest import get_annotations, get_fn


@pytest.fixture
def registered(mcp, patch_client):
    tags.register(mcp)
    return mcp, patch_client


@pytest.mark.asyncio
async def test_list_tags(registered):
    mcp, client = registered
    client.get.return_value = [{"id": "t1", "name": "Travel"}]

    result = await get_fn(mcp, "immich_tags_list")()

    client.get.assert_called_once_with("/api/tags")
    assert result[0]["name"] == "Travel"


@pytest.mark.asyncio
async def test_get_tag(registered):
    mcp, client = registered
    client.get.return_value = {"id": "t1", "name": "Travel"}

    result = await get_fn(mcp, "immich_tags_get")("t1")

    client.get.assert_called_once_with("/api/tags/t1")
    assert result["id"] == "t1"


@pytest.mark.asyncio
async def test_create_tag_minimal(registered):
    mcp, client = registered
    client.post.return_value = {"id": "t2", "name": "Travel/Japan"}

    await get_fn(mcp, "immich_tags_create")("Travel/Japan")

    client.post.assert_called_once_with("/api/tags", json={"name": "Travel/Japan"})


@pytest.mark.asyncio
async def test_create_tag_with_color(registered):
    mcp, client = registered
    client.post.return_value = {}

    await get_fn(mcp, "immich_tags_create")("Travel", color="#FF5733")

    _, kwargs = client.post.call_args
    assert kwargs["json"]["color"] == "#FF5733"


@pytest.mark.asyncio
async def test_update_tag(registered):
    mcp, client = registered
    client.put.return_value = {}

    await get_fn(mcp, "immich_tags_update")("t1", name="Adventure")

    client.put.assert_called_once_with("/api/tags/t1", json={"name": "Adventure"})


@pytest.mark.asyncio
async def test_delete_tag(registered):
    mcp, client = registered

    result = await get_fn(mcp, "immich_tags_delete")("t1")

    client.delete.assert_called_once_with("/api/tags/t1")
    assert result["deleted"] == "t1"


def test_delete_is_destructive(registered):
    mcp, _ = registered
    ann = get_annotations(mcp, "immich_tags_delete")
    assert ann.destructiveHint is True
    assert ann.idempotentHint is True


def test_list_is_readonly(registered):
    mcp, _ = registered
    ann = get_annotations(mcp, "immich_tags_list")
    assert ann.readOnlyHint is True
