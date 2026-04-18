from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from ..client import get_client


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        name="immich.ping",
        description="Verify connectivity and authentication with the Immich server. Returns server version and status.",
        annotations=ToolAnnotations(title="immich Ping Server", readOnlyHint=True, idempotentHint=True),
    )
    async def ping() -> dict:
        client = get_client()
        return await client.get("/api/server/about")

    @mcp.tool(
        name="immich.capabilities",
        description="Discover Immich server features and supported API capabilities.",
        annotations=ToolAnnotations(title="immich Server Capabilities", readOnlyHint=True, idempotentHint=True),
    )
    async def capabilities() -> dict:
        client = get_client()
        return await client.get("/api/server/features")
