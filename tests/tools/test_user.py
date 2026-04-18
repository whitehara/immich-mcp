import pytest
from immich_mcp.tools import user
from .conftest import get_annotations, get_fn


@pytest.fixture
def registered(mcp, patch_client):
    user.register(mcp)
    return mcp, patch_client


@pytest.mark.asyncio
async def test_me_calls_correct_endpoint(registered):
    mcp, client = registered
    client.get.return_value = {"id": "user-1", "email": "test@example.com", "name": "Test"}

    result = await get_fn(mcp, "immich_user_me")()

    client.get.assert_called_once_with("/api/users/me")
    assert result["email"] == "test@example.com"


def test_me_is_readonly(registered):
    mcp, _ = registered
    ann = get_annotations(mcp, "immich_user_me")
    assert ann.readOnlyHint is True
    assert ann.idempotentHint is True
