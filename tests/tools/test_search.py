import pytest
from immich_mcp.tools import search
from .conftest import get_annotations, get_fn


@pytest.fixture
def registered(mcp, patch_client):
    search.register(mcp)
    return mcp, patch_client


# --- immich.search.metadata ---

@pytest.mark.asyncio
async def test_metadata_search_minimal(registered):
    mcp, client = registered
    client.post.return_value = {"assets": {"items": []}}

    await get_fn(mcp, "immich.search.metadata")()

    client.post.assert_called_once()
    path, kwargs = client.post.call_args
    assert path[0] == "/api/search/metadata"
    assert kwargs["json"]["page"] == 1
    assert kwargs["json"]["size"] == 50


@pytest.mark.asyncio
async def test_metadata_search_with_filters(registered):
    mcp, client = registered
    client.post.return_value = {}

    await get_fn(mcp, "immich.search.metadata")(
        type="IMAGE",
        city="Tokyo",
        country="Japan",
        make="Sony",
        taken_after="2024-01-01",
        taken_before="2024-12-31",
        is_favorite=True,
    )

    _, kwargs = client.post.call_args
    body = kwargs["json"]
    assert body["type"] == "IMAGE"
    assert body["city"] == "Tokyo"
    assert body["country"] == "Japan"
    assert body["make"] == "Sony"
    assert body["takenAfter"] == "2024-01-01"
    assert body["takenBefore"] == "2024-12-31"
    assert body["isFavorite"] is True


@pytest.mark.asyncio
async def test_metadata_search_with_person(registered):
    mcp, client = registered
    client.post.return_value = {}

    await get_fn(mcp, "immich.search.metadata")(person_id="person-uuid")

    _, kwargs = client.post.call_args
    assert kwargs["json"]["personId"] == "person-uuid"


def test_metadata_is_readonly(registered):
    mcp, _ = registered
    ann = get_annotations(mcp, "immich.search.metadata")
    assert ann.readOnlyHint is True


# --- immich.search.smart ---

@pytest.mark.asyncio
async def test_smart_search_sends_query(registered):
    mcp, client = registered
    client.post.return_value = {"assets": {"items": []}}

    await get_fn(mcp, "immich.search.smart")("sunset at the beach")

    _, kwargs = client.post.call_args
    assert kwargs["json"]["query"] == "sunset at the beach"
    assert client.post.call_args[0][0] == "/api/search/smart"


@pytest.mark.asyncio
async def test_smart_search_with_type_filter(registered):
    mcp, client = registered
    client.post.return_value = {}

    await get_fn(mcp, "immich.search.smart")("birthday party", type="VIDEO")

    _, kwargs = client.post.call_args
    assert kwargs["json"]["type"] == "VIDEO"


def test_smart_is_readonly(registered):
    mcp, _ = registered
    ann = get_annotations(mcp, "immich.search.smart")
    assert ann.readOnlyHint is True


# --- immich.search.explore ---

@pytest.mark.asyncio
async def test_explore_calls_endpoint(registered):
    mcp, client = registered
    client.get.return_value = [{"fieldName": "city", "items": []}]

    result = await get_fn(mcp, "immich.search.explore")()

    client.get.assert_called_once_with("/api/search/explore")
    assert isinstance(result, list)


def test_explore_is_readonly_and_idempotent(registered):
    mcp, _ = registered
    ann = get_annotations(mcp, "immich.search.explore")
    assert ann.readOnlyHint is True
    assert ann.idempotentHint is True


# --- web_url in search results ---

@pytest.mark.asyncio
async def test_metadata_search_adds_web_url(registered):
    mcp, client = registered
    client.post.return_value = {
        "assets": {"items": [{"id": "a1"}, {"id": "a2"}], "total": 2}
    }

    result = await get_fn(mcp, "immich.search.metadata")()

    items = result["assets"]["items"]
    assert all("web_url" in item for item in items)
    assert "a1" in items[0]["web_url"]


@pytest.mark.asyncio
async def test_smart_search_adds_web_url(registered):
    mcp, client = registered
    client.post.return_value = {
        "assets": {"items": [{"id": "b1"}], "total": 1}
    }

    result = await get_fn(mcp, "immich.search.smart")("sunset")

    assert "web_url" in result["assets"]["items"][0]
