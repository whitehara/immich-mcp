import mimetypes
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Literal

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from ..client import get_client
from ..utils import asset_original_url, asset_thumbnail_url, asset_web_url

_AssetType = Literal["IMAGE", "VIDEO", "AUDIO", "OTHER"]


def _add_web_url(asset: dict) -> dict:
    if "id" in asset:
        asset["web_url"] = asset_web_url(asset["id"])
    return asset


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        name="immich_assets_list",
        description="List assets with optional filters. Returns paginated results.",
        annotations=ToolAnnotations(title="immich List Assets", readOnlyHint=True, idempotentHint=True),
    )
    async def assets_list(
        page: Annotated[int, Field(ge=1, description="Page number")] = 1,
        page_size: Annotated[int, Field(ge=1, le=1000, description="Results per page")] = 50,
        is_favorite: bool | None = None,
        is_archived: bool | None = None,
        is_trashed: bool | None = None,
        type: Annotated[_AssetType | None, Field(description="Filter by asset type")] = None,
    ) -> list:
        params: dict = {"page": page, "pageSize": page_size}
        if is_favorite is not None:
            params["isFavorite"] = is_favorite
        if is_archived is not None:
            params["isArchived"] = is_archived
        if is_trashed is not None:
            params["isTrashed"] = is_trashed
        if type is not None:
            params["type"] = type
        client = get_client()
        assets: list = await client.get("/api/assets", params=params)
        return [_add_web_url(a) for a in assets]

    @mcp.tool(
        name="immich_assets_get",
        description="Get full metadata for a single asset by its ID.",
        annotations=ToolAnnotations(title="immich Get Asset", readOnlyHint=True, idempotentHint=True),
    )
    async def assets_get(
        asset_id: Annotated[str, Field(description="Asset UUID")],
    ) -> dict:
        client = get_client()
        asset: dict = await client.get(f"/api/assets/{asset_id}")
        return _add_web_url(asset)

    @mcp.tool(
        name="immich_assets_view",
        description=(
            "Get direct URLs for viewing or downloading an asset. "
            "Returns thumbnail, original file, and Immich web UI links. "
            "URLs include the API key as a query parameter for direct browser access."
        ),
        annotations=ToolAnnotations(title="immich View Asset URLs", readOnlyHint=True, idempotentHint=True),
    )
    async def assets_view(
        asset_id: Annotated[str, Field(description="Asset UUID")],
    ) -> dict:
        return {
            "asset_id": asset_id,
            "thumbnail_url": asset_thumbnail_url(asset_id),
            "original_url": asset_original_url(asset_id),
            "web_url": asset_web_url(asset_id),
        }

    @mcp.tool(
        name="immich_assets_upload",
        description=(
            "Upload an asset to Immich from a local file path or a URL. "
            "For file paths, the MCP server process must have read access to the file. "
            "For URLs (http/https), the server downloads the file then uploads it to Immich."
        ),
        annotations=ToolAnnotations(title="immich Upload Asset"),
    )
    async def assets_upload(
        source: Annotated[str, Field(description="Local file path or http/https URL to upload")],
        device_asset_id: str = "",
        file_created_at: str = "",
        file_modified_at: str = "",
        is_favorite: bool = False,
    ) -> dict:
        is_url = source.startswith(("http://", "https://"))

        if is_url:
            async with httpx.AsyncClient() as http:
                response = await http.get(source)
                response.raise_for_status()
                file_content = response.content
                filename = source.rstrip("/").split("/")[-1].split("?")[0] or "upload"
                content_type = response.headers.get("content-type", "")
                mime_type = (
                    content_type.split(";")[0].strip()
                    or mimetypes.guess_type(filename)[0]
                    or "application/octet-stream"
                )
        else:
            path = Path(source)
            with open(path, "rb") as f:
                file_content = f.read()
            filename = path.name
            mime_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"

        now = datetime.now(timezone.utc).isoformat()
        data = {
            "deviceAssetId": device_asset_id or str(uuid.uuid4()),
            "deviceId": "immich-mcp",
            "fileCreatedAt": file_created_at or now,
            "fileModifiedAt": file_modified_at or now,
            "isFavorite": str(is_favorite).lower(),
        }
        files = {"assetData": (filename, file_content, mime_type)}

        client = get_client()
        result: dict = await client.post("/api/assets", files=files, data=data)
        return _add_web_url(result)

    @mcp.tool(
        name="immich_assets_update",
        description="Update metadata for a single asset (favorite, archived, description, rating).",
        annotations=ToolAnnotations(title="immich Update Asset", idempotentHint=True),
    )
    async def assets_update(
        asset_id: Annotated[str, Field(description="Asset UUID")],
        is_favorite: bool | None = None,
        is_archived: bool | None = None,
        description: str | None = None,
        rating: Annotated[int, Field(ge=0, le=5, description="Rating from 0 to 5")] | None = None,
    ) -> dict:
        body: dict = {}
        if is_favorite is not None:
            body["isFavorite"] = is_favorite
        if is_archived is not None:
            body["isArchived"] = is_archived
        if description is not None:
            body["description"] = description
        if rating is not None:
            body["rating"] = rating
        client = get_client()
        return await client.put(f"/api/assets/{asset_id}", json=body)

    @mcp.tool(
        name="immich_assets_bulk_update",
        description="Update metadata for multiple assets at once. Supports dry_run to preview changes.",
        annotations=ToolAnnotations(title="immich Bulk Update Assets", idempotentHint=True),
    )
    async def assets_bulk_update(
        asset_ids: Annotated[list[str], Field(description="List of asset UUIDs to update")],
        is_favorite: bool | None = None,
        is_archived: bool | None = None,
        rating: Annotated[int, Field(ge=0, le=5, description="Rating from 0 to 5")] | None = None,
        dry_run: Annotated[bool, Field(description="Preview changes without modifying any assets")] = True,
    ) -> dict:
        if dry_run:
            return {
                "dry_run": True,
                "affected_count": len(asset_ids),
                "asset_ids": asset_ids,
                "changes": {
                    k: v
                    for k, v in {
                        "isFavorite": is_favorite,
                        "isArchived": is_archived,
                        "rating": rating,
                    }.items()
                    if v is not None
                },
            }
        body: dict = {"ids": asset_ids}
        if is_favorite is not None:
            body["isFavorite"] = is_favorite
        if is_archived is not None:
            body["isArchived"] = is_archived
        if rating is not None:
            body["rating"] = rating
        client = get_client()
        return await client.put("/api/assets", json=body)

    @mcp.tool(
        name="immich_assets_delete",
        description="Delete one or more assets. Set force=true to permanently delete (skip trash). Always use dry_run=true first to preview.",
        annotations=ToolAnnotations(title="immich Delete Assets", destructiveHint=True, idempotentHint=True),
    )
    async def assets_delete(
        asset_ids: Annotated[list[str], Field(description="List of asset UUIDs to delete")],
        force: Annotated[bool, Field(description="Permanently delete, bypassing trash")] = False,
        dry_run: Annotated[bool, Field(description="Preview what would be deleted without making changes")] = True,
    ) -> dict:
        if dry_run:
            return {
                "dry_run": True,
                "affected_count": len(asset_ids),
                "asset_ids": asset_ids,
                "permanent": force,
            }
        client = get_client()
        await client.delete("/api/assets", json={"ids": asset_ids, "force": force})
        return {"deleted": len(asset_ids), "permanent": force}

    @mcp.tool(
        name="immich_assets_statistics",
        description="Get asset counts broken down by type (images, videos, total).",
        annotations=ToolAnnotations(title="immich Asset Statistics", readOnlyHint=True, idempotentHint=True),
    )
    async def assets_statistics() -> dict:
        client = get_client()
        return await client.get("/api/assets/statistics")
