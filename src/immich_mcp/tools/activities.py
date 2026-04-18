from typing import Annotated, Literal

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from ..client import get_client


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        name="immich.activities.list",
        description="List comments and likes for an album, optionally filtered by asset.",
        annotations=ToolAnnotations(title="List Activities", readOnlyHint=True, idempotentHint=True),
    )
    async def activities_list(
        album_id: Annotated[str, Field(description="Album UUID")],
        asset_id: str | None = None,
        type: Annotated[Literal["COMMENT", "LIKE"] | None, Field(description="Filter by activity type")] = None,
    ) -> list:
        params: dict = {"albumId": album_id}
        if asset_id:
            params["assetId"] = asset_id
        if type:
            params["type"] = type
        client = get_client()
        return await client.get("/api/activities", params=params)

    @mcp.tool(
        name="immich.activities.create",
        description="Add a comment or like to an album or specific asset within an album.",
        annotations=ToolAnnotations(title="Create Activity"),
    )
    async def activities_create(
        album_id: Annotated[str, Field(description="Album UUID")],
        type: Annotated[Literal["COMMENT", "LIKE"], Field(description="Activity type")],
        asset_id: str | None = None,
        comment: Annotated[str | None, Field(description="Comment text (required when type is COMMENT)")] = None,
    ) -> dict:
        body: dict = {"albumId": album_id, "type": type}
        if asset_id:
            body["assetId"] = asset_id
        if comment:
            body["comment"] = comment
        client = get_client()
        return await client.post("/api/activities", json=body)

    @mcp.tool(
        name="immich.activities.delete",
        description="Delete a comment or like by activity ID.",
        annotations=ToolAnnotations(title="Delete Activity", destructiveHint=True, idempotentHint=True),
    )
    async def activities_delete(
        activity_id: Annotated[str, Field(description="Activity UUID")],
    ) -> dict:
        client = get_client()
        await client.delete(f"/api/activities/{activity_id}")
        return {"deleted": activity_id}

    @mcp.tool(
        name="immich.activities.statistics",
        description="Get comment count for an album or specific asset within an album.",
        annotations=ToolAnnotations(title="Activity Statistics", readOnlyHint=True, idempotentHint=True),
    )
    async def activities_statistics(
        album_id: Annotated[str, Field(description="Album UUID")],
        asset_id: str | None = None,
    ) -> dict:
        params: dict = {"albumId": album_id}
        if asset_id:
            params["assetId"] = asset_id
        client = get_client()
        return await client.get("/api/activities/statistics", params=params)
