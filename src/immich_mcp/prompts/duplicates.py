from mcp.server.fastmcp import FastMCP


def register(mcp: FastMCP) -> None:
    @mcp.prompt(name="immich/review_duplicates")
    def review_duplicates() -> str:
        return """
Review and safely clean up duplicate photos in the Immich library.

## Steps

1. Call `immich.duplicates.list` with `analyze=true` to get duplicate groups
   with pre-computed keep/delete recommendations.

   **Important**: On first call after server start, the response will have
   `cache_ready=false` and `status="prefetching"` while data loads in the background.
   Large libraries (70k+ assets) may take 20–30 minutes on first load.
   Wait and call again until `cache_ready=true`.

   Results are **paginated** (default 50 groups/page). Check `total_pages` in the
   response and call again with `page=2`, `page=3`, etc. to retrieve all groups.

2. For each duplicate group, evaluate the analysis:
   - `keep_id`: the asset recommended to keep (highest quality/priority)
   - `safe_to_delete_ids`: assets safe to delete (not favorited, not in any album)
   - `protected_ids`: assets that are favorited or album members — require explicit user approval
   - `needs_review`: true when protected assets are present in the delete candidates

3. Present a summary to the user before any deletion:
   - Total groups found
   - How many assets are safe to delete automatically
   - Which groups need manual review (protected assets)
   - For protected assets, show: asset ID, favorite status, album names

4. For each group, ask the user to choose one of the following actions:

   **a) Delete duplicates** — keep the best asset, delete the rest
      - Call `immich.duplicates.delete` with `dry_run=true` first to confirm
      - Then call with `dry_run=false` to execute
      - Use `force=false` (trash) unless the user explicitly requests permanent deletion

   **b) Dismiss duplicates** — assets are intentionally kept as separate copies
      - Use this when the user considers the "duplicates" to be distinct files they want to keep
      - Call `immich.duplicates.dismiss` with the `duplicate_id` of the group
      - The assets are NOT deleted; only the duplicate grouping is removed
      - They will no longer appear in the duplicate list

## Decision Rules

| Condition | Action |
|-----------|--------|
| `isFavorite=true` | Never delete without explicit user approval |
| `albums` not empty | Never delete without explicit user approval |
| `livePhotoVideoId` present | Keep the Live Photo pair together |
| Format: RAW/DNG > HEIC > PNG > JPEG | Prefer higher-quality format |
| Same format, larger file/resolution | Prefer higher quality |
| `isTrashed=true` | Safe to permanently delete (already in trash) |
| User wants to keep all copies | Dismiss the group (`immich.duplicates.dismiss`) |

## Edge Cases to Flag

- Both assets in a group are favorited → ask user: delete one or dismiss?
- Both assets are in albums → ask user: delete one or dismiss?
- File size difference < 5% with same format → uncertain quality difference, flag for review
- More than 2 assets in a group → show all options to user before deciding
"""
