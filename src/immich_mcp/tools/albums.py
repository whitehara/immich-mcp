from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from ..client import get_client
from ..utils import album_web_url, asset_web_url


def _add_album_web_url(album: dict) -> dict:
    if "id" in album:
        album["web_url"] = album_web_url(album["id"])
    for asset in album.get("assets", []):
        if "id" in asset:
            asset["web_url"] = asset_web_url(asset["id"])
    return album


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        name="immich.albums.list",
        description="List all albums. Optionally filter by shared status.",
        annotations=ToolAnnotations(title="immich: List Albums", readOnlyHint=True, idempotentHint=True),
    )
    async def albums_list(shared: bool | None = None) -> list:
        params: dict = {}
        if shared is not None:
            params["shared"] = shared
        client = get_client()
        albums: list = await client.get("/api/albums", params=params)
        return [_add_album_web_url(a) for a in albums]

    @mcp.tool(
        name="immich.albums.get",
        description="Get full details of an album including its assets.",
        annotations=ToolAnnotations(title="immich: Get Album", readOnlyHint=True, idempotentHint=True),
    )
    async def albums_get(
        album_id: Annotated[str, Field(description="Album UUID")],
        without_assets: bool = False,
    ) -> dict:
        client = get_client()
        album: dict = await client.get(
            f"/api/albums/{album_id}", params={"withoutAssets": without_assets}
        )
        return _add_album_web_url(album)

    @mcp.tool(
        name="immich.albums.create",
        description="Create a new album with an optional list of asset IDs.",
        annotations=ToolAnnotations(title="immich: Create Album"),
    )
    async def albums_create(
        album_name: Annotated[str, Field(min_length=1, description="Album name")],
        description: str | None = None,
        asset_ids: list[str] | None = None,
    ) -> dict:
        body: dict = {"albumName": album_name}
        if description:
            body["description"] = description
        if asset_ids:
            body["assetIds"] = asset_ids
        client = get_client()
        album: dict = await client.post("/api/albums", json=body)
        return _add_album_web_url(album)

    @mcp.tool(
        name="immich.albums.update",
        description="Update album metadata: name, description, or cover asset.",
        annotations=ToolAnnotations(title="immich: Update Album", idempotentHint=True),
    )
    async def albums_update(
        album_id: Annotated[str, Field(description="Album UUID")],
        album_name: str | None = None,
        description: str | None = None,
        album_thumbnail_asset_id: str | None = None,
    ) -> dict:
        body: dict = {}
        if album_name:
            body["albumName"] = album_name
        if description is not None:
            body["description"] = description
        if album_thumbnail_asset_id:
            body["albumThumbnailAssetId"] = album_thumbnail_asset_id
        client = get_client()
        return await client.patch(f"/api/albums/{album_id}", json=body)

    @mcp.tool(
        name="immich.albums.delete",
        description="Delete an album. This does not delete the assets inside it.",
        annotations=ToolAnnotations(title="immich: Delete Album", destructiveHint=True, idempotentHint=True),
    )
    async def albums_delete(
        album_id: Annotated[str, Field(description="Album UUID")],
    ) -> dict:
        client = get_client()
        await client.delete(f"/api/albums/{album_id}")
        return {"deleted": album_id}

    @mcp.tool(
        name="immich.albums.add_assets",
        description="Add one or more assets to an album.",
        annotations=ToolAnnotations(title="immich: Add Assets to Album", idempotentHint=True),
    )
    async def albums_add_assets(
        album_id: Annotated[str, Field(description="Album UUID")],
        asset_ids: Annotated[list[str], Field(description="List of asset UUIDs to add")],
    ) -> dict:
        client = get_client()
        return await client.put(f"/api/albums/{album_id}/assets", json={"ids": asset_ids})

    @mcp.tool(
        name="immich.albums.remove_assets",
        description="Remove one or more assets from an album. The assets themselves are not deleted.",
        annotations=ToolAnnotations(title="immich: Remove Assets from Album", idempotentHint=True),
    )
    async def albums_remove_assets(
        album_id: Annotated[str, Field(description="Album UUID")],
        asset_ids: Annotated[list[str], Field(description="List of asset UUIDs to remove")],
    ) -> dict:
        client = get_client()
        return await client.delete(
            f"/api/albums/{album_id}/assets", json={"ids": asset_ids}
        )
