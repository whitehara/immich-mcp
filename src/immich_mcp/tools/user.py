from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from ..client import get_client


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        name="immich_user_me",
        description="Get the profile of the currently authenticated user (name, email, quota, role).",
        annotations=ToolAnnotations(title="immich My Profile", readOnlyHint=True, idempotentHint=True),
    )
    async def user_me() -> dict:
        client = get_client()
        return await client.get("/api/users/me")
