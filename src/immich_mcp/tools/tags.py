from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from ..client import get_client


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        name="immich.tags.list",
        description="List all tags in the library.",
        annotations=ToolAnnotations(title="immich: List Tags", readOnlyHint=True, idempotentHint=True),
    )
    async def tags_list() -> list:
        client = get_client()
        return await client.get("/api/tags")

    @mcp.tool(
        name="immich.tags.get",
        description="Get details of a specific tag by ID.",
        annotations=ToolAnnotations(title="immich: Get Tag", readOnlyHint=True, idempotentHint=True),
    )
    async def tags_get(
        tag_id: Annotated[str, Field(description="Tag UUID")],
    ) -> dict:
        client = get_client()
        return await client.get(f"/api/tags/{tag_id}")

    @mcp.tool(
        name="immich.tags.create",
        description="Create a new tag. Use '/' as separator for nested tags (e.g. 'Travel/Japan').",
        annotations=ToolAnnotations(title="immich: Create Tag"),
    )
    async def tags_create(
        name: Annotated[str, Field(min_length=1, description="Tag name; use '/' for nested tags e.g. 'Travel/Japan'")],
        color: str | None = None,
    ) -> dict:
        body: dict = {"name": name}
        if color:
            body["color"] = color
        client = get_client()
        return await client.post("/api/tags", json=body)

    @mcp.tool(
        name="immich.tags.update",
        description="Update a tag's name or color.",
        annotations=ToolAnnotations(title="immich: Update Tag", idempotentHint=True),
    )
    async def tags_update(
        tag_id: Annotated[str, Field(description="Tag UUID")],
        name: str | None = None,
        color: str | None = None,
    ) -> dict:
        body: dict = {}
        if name:
            body["name"] = name
        if color:
            body["color"] = color
        client = get_client()
        return await client.put(f"/api/tags/{tag_id}", json=body)

    @mcp.tool(
        name="immich.tags.delete",
        description="Delete a tag by ID.",
        annotations=ToolAnnotations(title="immich: Delete Tag", destructiveHint=True, idempotentHint=True),
    )
    async def tags_delete(
        tag_id: Annotated[str, Field(description="Tag UUID")],
    ) -> dict:
        client = get_client()
        await client.delete(f"/api/tags/{tag_id}")
        return {"deleted": tag_id}
