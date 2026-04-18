from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

import httpx

from .config import get_settings

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


class ImmichClient:
    def __init__(self) -> None:
        s = get_settings()
        self._http = httpx.AsyncClient(
            base_url=s.base_url.rstrip("/"),
            headers={"x-api-key": s.api_key, "Accept": "application/json"},
            timeout=s.timeout,
            transport=httpx.AsyncHTTPTransport(retries=s.max_retries),
        )

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        response = await self._http.request(method, path, **kwargs)
        response.raise_for_status()
        return response.json() if response.content else None

    async def get(self, path: str, **kwargs: Any) -> Any:
        return await self._request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs: Any) -> Any:
        return await self._request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs: Any) -> Any:
        return await self._request("PUT", path, **kwargs)

    async def patch(self, path: str, **kwargs: Any) -> Any:
        return await self._request("PATCH", path, **kwargs)

    async def delete(self, path: str, **kwargs: Any) -> Any:
        return await self._request("DELETE", path, **kwargs)

    async def aclose(self) -> None:
        await self._http.aclose()


_client: ImmichClient | None = None


def get_client() -> ImmichClient:
    global _client
    if _client is None:
        _client = ImmichClient()
    return _client


@asynccontextmanager
async def managed_client(server: "FastMCP") -> AsyncIterator[None]:
    """FastMCP lifespan: initialize and cleanly close the ImmichClient."""
    global _client
    _client = ImmichClient()
    try:
        yield
    finally:
        await _client.aclose()
        _client = None
