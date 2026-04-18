from typing import Annotated, Literal

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from ..client import get_client
from ..utils import asset_web_url

_AssetType = Literal["IMAGE", "VIDEO", "AUDIO", "OTHER"]


def _add_web_url_to_items(result: dict) -> dict:
    items = result.get("assets", {}).get("items", [])
    for asset in items:
        if "id" in asset:
            asset["web_url"] = asset_web_url(asset["id"])
    return result


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        name="immich.search.metadata",
        description="Search assets using metadata filters: date range, type, location, camera model, person, filename.",
        annotations=ToolAnnotations(title="Metadata Search", readOnlyHint=True),
    )
    async def search_metadata(
        query: str | None = None,
        type: Annotated[_AssetType | None, Field(description="Filter by asset type")] = None,
        is_favorite: bool | None = None,
        is_archived: bool | None = None,
        city: str | None = None,
        country: str | None = None,
        make: str | None = None,
        model: str | None = None,
        person_id: str | None = None,
        taken_after: Annotated[str | None, Field(description="ISO 8601 date, e.g. 2024-01-01")] = None,
        taken_before: Annotated[str | None, Field(description="ISO 8601 date, e.g. 2024-12-31")] = None,
        page: Annotated[int, Field(ge=1, description="Page number")] = 1,
        page_size: Annotated[int, Field(ge=1, le=1000, description="Results per page")] = 50,
    ) -> dict:
        body: dict = {"page": page, "size": page_size}
        if query:
            body["originalFileName"] = query
        if type:
            body["type"] = type
        if is_favorite is not None:
            body["isFavorite"] = is_favorite
        if is_archived is not None:
            body["isArchived"] = is_archived
        if city:
            body["city"] = city
        if country:
            body["country"] = country
        if make:
            body["make"] = make
        if model:
            body["model"] = model
        if person_id:
            body["personId"] = person_id
        if taken_after:
            body["takenAfter"] = taken_after
        if taken_before:
            body["takenBefore"] = taken_before
        client = get_client()
        result = await client.post("/api/search/metadata", json=body)
        return _add_web_url_to_items(result)

    @mcp.tool(
        name="immich.search.smart",
        description="Semantic search using CLIP/ML. Describe what you're looking for in natural language (e.g. 'sunset at the beach', 'birthday party').",
        annotations=ToolAnnotations(title="Smart Search", readOnlyHint=True),
    )
    async def search_smart(
        query: Annotated[str, Field(min_length=1, description="Natural language description of what to find")],
        type: Annotated[_AssetType | None, Field(description="Filter by asset type")] = None,
        is_favorite: bool | None = None,
        page: Annotated[int, Field(ge=1, description="Page number")] = 1,
        page_size: Annotated[int, Field(ge=1, le=1000, description="Results per page")] = 50,
    ) -> dict:
        body: dict = {"query": query, "page": page, "size": page_size}
        if type:
            body["type"] = type
        if is_favorite is not None:
            body["isFavorite"] = is_favorite
        client = get_client()
        result = await client.post("/api/search/smart", json=body)
        return _add_web_url_to_items(result)

    @mcp.tool(
        name="immich.search.explore",
        description="Get discovery data: popular places, recognized people, and notable things in your library.",
        annotations=ToolAnnotations(title="Explore Library", readOnlyHint=True, idempotentHint=True),
    )
    async def search_explore() -> list:
        client = get_client()
        return await client.get("/api/search/explore")
