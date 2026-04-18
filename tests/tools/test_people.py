import pytest
from immich_mcp.tools import people
from .conftest import get_annotations, get_fn


@pytest.fixture
def registered(mcp, patch_client):
    people.register(mcp)
    return mcp, patch_client


@pytest.mark.asyncio
async def test_list_people_defaults(registered):
    mcp, client = registered
    client.get.return_value = {"people": [], "total": 0}

    await get_fn(mcp, "immich_people_list")()

    client.get.assert_called_once_with(
        "/api/people", params={"page": 1, "size": 50, "withHidden": False}
    )


@pytest.mark.asyncio
async def test_list_people_with_hidden(registered):
    mcp, client = registered
    client.get.return_value = {}

    await get_fn(mcp, "immich_people_list")(with_hidden=True)

    _, kwargs = client.get.call_args
    assert kwargs["params"]["withHidden"] is True


@pytest.mark.asyncio
async def test_get_person(registered):
    mcp, client = registered
    client.get.return_value = {"id": "p1", "name": "Alice"}

    result = await get_fn(mcp, "immich_people_get")("p1")

    client.get.assert_called_once_with("/api/people/p1")
    assert result["name"] == "Alice"


@pytest.mark.asyncio
async def test_update_person_name(registered):
    mcp, client = registered
    client.put.return_value = {}

    await get_fn(mcp, "immich_people_update")("p1", name="Alice")

    client.put.assert_called_once_with("/api/people/p1", json={"name": "Alice"})


@pytest.mark.asyncio
async def test_update_person_hide(registered):
    mcp, client = registered
    client.put.return_value = {}

    await get_fn(mcp, "immich_people_update")("p1", is_hidden=True)

    _, kwargs = client.put.call_args
    assert kwargs["json"] == {"isHidden": True}


@pytest.mark.asyncio
async def test_merge_people(registered):
    mcp, client = registered
    client.post.return_value = [{"success": True}]

    await get_fn(mcp, "immich_people_merge")("target-id", "source-id")

    client.post.assert_called_once_with(
        "/api/people/target-id/merge", json={"ids": ["source-id"]}
    )


def test_merge_is_destructive(registered):
    mcp, _ = registered
    ann = get_annotations(mcp, "immich_people_merge")
    assert ann.destructiveHint is True


@pytest.mark.asyncio
async def test_statistics(registered):
    mcp, client = registered
    client.get.return_value = {"assets": 42}

    result = await get_fn(mcp, "immich_people_statistics")("p1")

    client.get.assert_called_once_with("/api/people/p1/statistics")
    assert result["assets"] == 42


def test_list_is_readonly(registered):
    mcp, _ = registered
    ann = get_annotations(mcp, "immich_people_list")
    assert ann.readOnlyHint is True
    assert ann.idempotentHint is True
