import os

# Must be set before any immich_mcp imports occur during test collection.
os.environ.setdefault("IMMICH_BASE_URL", "https://immich.test")
os.environ.setdefault("IMMICH_API_KEY", "test-api-key")

import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.get = AsyncMock(return_value={})
    client.post = AsyncMock(return_value={})
    client.put = AsyncMock(return_value={})
    client.patch = AsyncMock(return_value={})
    client.delete = AsyncMock(return_value=None)
    return client


@pytest.fixture
def patch_client(mock_client, monkeypatch):
    """Inject mock_client as the ImmichClient singleton so all tools use it."""
    import immich_mcp.client as client_module
    monkeypatch.setattr(client_module, "_client", mock_client)
    return mock_client
