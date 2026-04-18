import asyncio
import time
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from ..client import get_client
from ..utils import asset_web_url

# Ordered from highest to lowest quality; first matching fragment wins.
# Fragments are matched as substrings of the lowercased MIME type.
_FORMAT_PRIORITY: tuple[tuple[int, tuple[str, ...]], ...] = (
    (100, ("dng", "x-canon-cr2", "x-nikon-nef", "x-panasonic-raw", "x-sony-arw", "x-raw")),
    (80,  ("heic", "heif")),
    (70,  ("png", "tiff")),
    (50,  ("jpeg", "jpg")),
    (40,  ("webp",)),
    (30,  ("gif",)),
)

# Background-fetch cache for /api/duplicates.
# /api/duplicates on large libraries (70k+ assets) takes 1–2 minutes, which
# exceeds the ~30-second Cloudflare AI gateway timeout.  We fetch once in the
# background so subsequent tool calls return instantly from memory.
_cache: list | None = None
_cache_fetch_time: float = 0.0
_prefetch_task: "asyncio.Task[None] | None" = None
_CACHE_TTL: float = 3600.0  # seconds before a background refresh is triggered


async def _fetch_into_cache() -> None:
    global _cache, _cache_fetch_time
    client = get_client()
    _cache = await client.get("/api/duplicates")
    _cache_fetch_time = time.monotonic()


def _format_score(mime_type: str | None) -> int:
    if not mime_type:
        return 0
    lower = mime_type.lower()
    for score, fragments in _FORMAT_PRIORITY:
        if any(f in lower for f in fragments):
            return score
    return 10


def _analyze_group(assets: list[dict]) -> dict:
    """Determine keep/delete recommendations for a duplicate group."""
    recommendations = []
    for asset in assets:
        exif = asset.get("exifInfo") or {}
        width = exif.get("exifImageWidth") or exif.get("imageWidth") or 0
        height = exif.get("exifImageHeight") or exif.get("imageHeight") or 0
        score = {
            "id": asset["id"],
            "format_score": _format_score(asset.get("originalMimeType")),
            "file_size": asset.get("fileSize") or 0,
            "resolution": width * height,
            "is_favorite": asset.get("isFavorite", False),
            "album_count": len(asset.get("albums") or []),
            "has_live_photo": bool(asset.get("livePhotoVideoId")),
            "is_trashed": asset.get("isTrashed", False),
        }
        recommendations.append(score)

    # Quality metrics determine keep_id; favorites and album membership are tiebreakers only.
    # This ensures the highest-quality asset is recommended to keep, while favorites/album
    # members among delete candidates are flagged as protected (requiring user review).
    recommendations.sort(
        key=lambda x: (
            x["has_live_photo"],
            x["format_score"],
            x["resolution"],
            x["file_size"],
            x["is_favorite"],
            x["album_count"],
        ),
        reverse=True,
    )

    keep = recommendations[0]
    delete_candidates = recommendations[1:]

    protected = [
        r for r in delete_candidates if r["is_favorite"] or r["album_count"] > 0
    ]
    safe_to_delete = [r for r in delete_candidates if not r["is_favorite"] and r["album_count"] == 0]

    return {
        "keep_id": keep["id"],
        "safe_to_delete_ids": [r["id"] for r in safe_to_delete],
        "protected_ids": [r["id"] for r in protected],
        "needs_review": len(protected) > 0,
    }


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        name="immich.duplicates.list",
        description=(
            "List all duplicate asset groups detected by Immich. "
            "Each group contains assets with matching content hashes. "
            "Returns full metadata needed for deletion decisions: "
            "file format, size, resolution, favorite status, album membership, Live Photo status. "
            "Results are served from an in-memory cache (refreshed every hour). "
            "On first call after server start the cache is empty: the response will have "
            "cache_ready=false and status='prefetching' while data loads in the background — "
            "call again in 1–2 minutes."
        ),
        annotations=ToolAnnotations(title="List Duplicates", readOnlyHint=True, idempotentHint=True),
    )
    async def duplicates_list(
        analyze: Annotated[bool, Field(description="Include keep/delete recommendations for each group")] = True,
    ) -> dict:
        global _prefetch_task

        if _cache is None:
            # No data yet — kick off background fetch and return immediately.
            if _prefetch_task is None or _prefetch_task.done():
                _prefetch_task = asyncio.create_task(_fetch_into_cache())
            return {
                "cache_ready": False,
                "status": "prefetching",
                "message": (
                    "Duplicate data is being fetched from Immich in the background "
                    "(large libraries take 1–2 minutes). Call this tool again shortly."
                ),
            }

        # Cache is stale — refresh silently in the background while serving current data.
        if (time.monotonic() - _cache_fetch_time) >= _CACHE_TTL:
            if _prefetch_task is None or _prefetch_task.done():
                _prefetch_task = asyncio.create_task(_fetch_into_cache())

        raw = _cache
        groups = []
        for entry in raw:
            entry_assets = entry.get("assets", [])
            for asset in entry_assets:
                if "id" in asset:
                    asset["web_url"] = asset_web_url(asset["id"])
            group: dict = {
                "duplicate_id": entry.get("duplicateId"),
                "assets": entry_assets,
            }
            if analyze:
                group["analysis"] = _analyze_group(entry_assets)
            groups.append(group)

        return {
            "cache_ready": True,
            "total_groups": len(groups),
            "total_duplicates": sum(len(g["assets"]) for g in groups),
            "groups": groups,
        }

    @mcp.tool(
        name="immich.duplicates.delete",
        description=(
            "Delete specific assets from duplicate groups. "
            "Always run with dry_run=true first to confirm what will be deleted. "
            "Set force=true to permanently delete (bypass trash). "
            "Do NOT delete assets that are favorited or belong to albums without explicit user approval."
        ),
        annotations=ToolAnnotations(title="Delete Duplicate Assets", destructiveHint=True, idempotentHint=True),
    )
    async def duplicates_delete(
        asset_ids: Annotated[list[str], Field(description="Asset UUIDs to delete")],
        force: Annotated[bool, Field(description="Permanently delete, bypassing trash")] = False,
        dry_run: Annotated[bool, Field(description="Preview what would be deleted without making changes")] = True,
    ) -> dict:
        if dry_run:
            return {
                "dry_run": True,
                "would_delete_count": len(asset_ids),
                "asset_ids": asset_ids,
                "permanent": force,
                "message": "Set dry_run=false to execute deletion.",
            }

        client = get_client()
        await client.delete("/api/assets", json={"ids": asset_ids, "force": force})
        return {
            "deleted_count": len(asset_ids),
            "asset_ids": asset_ids,
            "permanent": force,
        }

    @mcp.tool(
        name="immich.duplicates.dismiss",
        description=(
            "Dismiss duplicate groups without deleting any assets. "
            "Use this when the assets are intentionally kept as separate copies "
            "and should no longer appear in the duplicate list. "
            "The asset files are NOT deleted — only the duplicate grouping is removed. "
            "Always run with dry_run=true first."
        ),
        annotations=ToolAnnotations(title="Dismiss Duplicates", destructiveHint=True, idempotentHint=True),
    )
    async def duplicates_dismiss(
        duplicate_ids: Annotated[list[str], Field(description="Duplicate group IDs to dismiss")],
        dry_run: Annotated[bool, Field(description="Preview what would be dismissed without making changes")] = True,
    ) -> dict:
        if dry_run:
            return {
                "dry_run": True,
                "would_dismiss_count": len(duplicate_ids),
                "duplicate_ids": duplicate_ids,
                "message": "Set dry_run=false to execute dismissal.",
            }

        client = get_client()
        await client.delete("/api/duplicates", json={"ids": duplicate_ids})
        return {
            "dismissed_count": len(duplicate_ids),
            "duplicate_ids": duplicate_ids,
        }
