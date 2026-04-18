from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from ..client import get_client


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        name="immich.people.list",
        description="List all recognized people from face recognition. Supports pagination.",
        annotations=ToolAnnotations(title="List People", readOnlyHint=True, idempotentHint=True),
    )
    async def people_list(
        page: Annotated[int, Field(ge=1, description="Page number")] = 1,
        page_size: Annotated[int, Field(ge=1, le=1000, description="Results per page")] = 50,
        with_hidden: bool = False,
    ) -> dict:
        client = get_client()
        return await client.get(
            "/api/people",
            params={"page": page, "size": page_size, "withHidden": with_hidden},
        )

    @mcp.tool(
        name="immich.people.get",
        description="Get details for a specific person by ID.",
        annotations=ToolAnnotations(title="Get Person", readOnlyHint=True, idempotentHint=True),
    )
    async def people_get(
        person_id: Annotated[str, Field(description="Person UUID")],
    ) -> dict:
        client = get_client()
        return await client.get(f"/api/people/{person_id}")

    @mcp.tool(
        name="immich.people.update",
        description="Update a person's name or visibility (hidden/visible).",
        annotations=ToolAnnotations(title="Update Person", idempotentHint=True),
    )
    async def people_update(
        person_id: Annotated[str, Field(description="Person UUID")],
        name: str | None = None,
        is_hidden: bool | None = None,
    ) -> dict:
        body: dict = {}
        if name is not None:
            body["name"] = name
        if is_hidden is not None:
            body["isHidden"] = is_hidden
        client = get_client()
        return await client.put(f"/api/people/{person_id}", json=body)

    @mcp.tool(
        name="immich.people.merge",
        description="Merge two person clusters into one. The source person will be merged into the target.",
        annotations=ToolAnnotations(title="Merge People", destructiveHint=True),
    )
    async def people_merge(
        target_person_id: Annotated[str, Field(description="Person UUID to merge into")],
        source_person_id: Annotated[str, Field(description="Person UUID to merge from (will be removed)")],
    ) -> dict:
        client = get_client()
        return await client.post(
            f"/api/people/{target_person_id}/merge",
            json={"ids": [source_person_id]},
        )

    @mcp.tool(
        name="immich.people.statistics",
        description="Get asset count statistics for a specific person.",
        annotations=ToolAnnotations(title="Person Statistics", readOnlyHint=True, idempotentHint=True),
    )
    async def people_statistics(
        person_id: Annotated[str, Field(description="Person UUID")],
    ) -> dict:
        client = get_client()
        return await client.get(f"/api/people/{person_id}/statistics")
