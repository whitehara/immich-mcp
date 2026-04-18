from typing import Annotated, Literal

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from ..client import get_client


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        name="immich.shared_links.list",
        description="List all shared links.",
        annotations=ToolAnnotations(title="immich List Shared Links", readOnlyHint=True, idempotentHint=True),
    )
    async def shared_links_list() -> list:
        client = get_client()
        return await client.get("/api/shared-links")

    @mcp.tool(
        name="immich.shared_links.get",
        description="Get details of a specific shared link by ID.",
        annotations=ToolAnnotations(title="immich Get Shared Link", readOnlyHint=True, idempotentHint=True),
    )
    async def shared_links_get(
        shared_link_id: Annotated[str, Field(description="Shared link UUID")],
    ) -> dict:
        client = get_client()
        return await client.get(f"/api/shared-links/{shared_link_id}")

    @mcp.tool(
        name="immich.shared_links.create",
        description="Create a shareable link for an album or specific assets. Optionally set expiry and password.",
        annotations=ToolAnnotations(title="immich Create Shared Link"),
    )
    async def shared_links_create(
        type: Annotated[Literal["ALBUM", "INDIVIDUAL"], Field(description="Share an album or individual assets")],
        album_id: str | None = None,
        asset_ids: list[str] | None = None,
        expires_at: Annotated[str | None, Field(description="Expiry datetime in ISO 8601 format")] = None,
        allow_download: bool = True,
        allow_upload: bool = False,
        show_metadata: bool = True,
        password: str | None = None,
        description: str | None = None,
    ) -> dict:
        body: dict = {
            "type": type,
            "allowDownload": allow_download,
            "allowUpload": allow_upload,
            "showMetadata": show_metadata,
        }
        if album_id:
            body["albumId"] = album_id
        if asset_ids:
            body["assetIds"] = asset_ids
        if expires_at:
            body["expiresAt"] = expires_at
        if password:
            body["password"] = password
        if description:
            body["description"] = description
        client = get_client()
        return await client.post("/api/shared-links", json=body)

    @mcp.tool(
        name="immich.shared_links.update",
        description="Update shared link settings: expiry, password, download permission.",
        annotations=ToolAnnotations(title="immich Update Shared Link", idempotentHint=True),
    )
    async def shared_links_update(
        shared_link_id: Annotated[str, Field(description="Shared link UUID")],
        expires_at: Annotated[str | None, Field(description="Expiry datetime in ISO 8601 format")] = None,
        allow_download: bool | None = None,
        allow_upload: bool | None = None,
        show_metadata: bool | None = None,
        password: str | None = None,
        description: str | None = None,
    ) -> dict:
        body: dict = {}
        if expires_at is not None:
            body["expiresAt"] = expires_at
        if allow_download is not None:
            body["allowDownload"] = allow_download
        if allow_upload is not None:
            body["allowUpload"] = allow_upload
        if show_metadata is not None:
            body["showMetadata"] = show_metadata
        if password is not None:
            body["password"] = password
        if description is not None:
            body["description"] = description
        client = get_client()
        return await client.patch(f"/api/shared-links/{shared_link_id}", json=body)

    @mcp.tool(
        name="immich.shared_links.remove",
        description="Remove a shared link, revoking access to its content.",
        annotations=ToolAnnotations(title="immich Remove Shared Link", destructiveHint=True, idempotentHint=True),
    )
    async def shared_links_remove(
        shared_link_id: Annotated[str, Field(description="Shared link UUID")],
    ) -> dict:
        client = get_client()
        await client.delete(f"/api/shared-links/{shared_link_id}")
        return {"removed": shared_link_id}
