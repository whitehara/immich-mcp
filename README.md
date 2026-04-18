# immich-mcp

MCP server for [Immich](https://immich.app/) photo management. Provides AI-accessible tools for browsing, searching, organizing, and managing your self-hosted photo library — including duplicate detection and safe deletion workflows.

## Features

- **40+ MCP tools** covering assets, albums, search, people, tags, shared links, activities, and duplicates
- **3 MCP prompts** for guided workflows: duplicate review, album organization, and untagged photo discovery
- **Tool annotations** (`title`, `readOnlyHint`, `destructiveHint`, `idempotentHint`) for safe AI-driven automation
- **Dry-run support** on all destructive operations
- **Duplicate analysis** with format priority scoring and protection for favorited/album-linked assets
- **Automatic retries** via `httpx.AsyncHTTPTransport` (configurable via `IMMICH_MAX_RETRIES`)

## Requirements

- Python 3.11+
- Immich server with API access
- `uv` (recommended) or `pip`

## Installation

```bash
git clone https://github.com/whitehara/immich-mcp
cd immich-mcp
uv pip install -e .
```

## Configuration

Set environment variables before running:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `IMMICH_BASE_URL` | Yes | — | Immich server URL (e.g. `https://photos.example.com`) |
| `IMMICH_API_KEY` | Yes | — | API key from Immich → Account Settings → API Keys |
| `IMMICH_EXTERNAL_URL` | No | same as `IMMICH_BASE_URL` | Public URL used for `web_url` links (useful when base URL is internal) |
| `IMMICH_TIMEOUT` | No | `30.0` | HTTP timeout in seconds. The `/api/duplicates` endpoint on large libraries (70k+ assets) can exceed 30 s — set to `120.0` or higher if `immich_duplicates_list` times out. |
| `IMMICH_MAX_RETRIES` | No | `3` | Retry attempts on transient errors |

### Immich API Key Permissions

Immich 1.138.0+ supports granular API key permissions. Grant the following scopes when creating your key (Immich → Account Settings → API Keys → Create).

For **full functionality** (all tools enabled):

| Scope | Required by |
|-------|-------------|
| `server.about` | `immich_ping` |
| `user.read` | `immich_user_me` |
| `asset.read` | `immich_assets_list/get/view`, all search tools |
| `asset.upload` | `immich_assets_upload` |
| `asset.update` | `immich_assets_update`, `immich_assets_bulk_update` |
| `asset.delete` | `immich_assets_delete`, `immich_duplicates_delete` |
| `asset.statistics` | `immich_assets_statistics` |
| `album.read` | `immich_albums_list/get` |
| `album.create` | `immich_albums_create` |
| `album.update` | `immich_albums_update` |
| `album.delete` | `immich_albums_delete` |
| `albumAsset.create` | `immich_albums_add_assets` |
| `albumAsset.delete` | `immich_albums_remove_assets` |
| `person.read` | `immich_people_list/get` |
| `person.update` | `immich_people_update` |
| `person.merge` | `immich_people_merge` |
| `person.statistics` | `immich_people_statistics` |
| `tag.read` | `immich_tags_list/get` |
| `tag.create` | `immich_tags_create` |
| `tag.update` | `immich_tags_update` |
| `tag.delete` | `immich_tags_delete` |
| `sharedLink.read` | `immich_shared_links_list/get` |
| `sharedLink.create` | `immich_shared_links_create` |
| `sharedLink.update` | `immich_shared_links_update` |
| `sharedLink.delete` | `immich_shared_links_remove` |
| `activity.read` | `immich_activities_list` |
| `activity.statistics` | `immich_activities_statistics` |
| `activity.create` | `immich_activities_create` |
| `activity.delete` | `immich_activities_delete` |
| `duplicate.read` | `immich_duplicates_list` |
| `duplicate.delete` | `immich_duplicates_dismiss` |

For **read-only use** (no create/update/delete tools), grant only:
`server.about`, `user.read`, `asset.read`, `asset.statistics`, `album.read`, `person.read`, `person.statistics`, `tag.read`, `sharedLink.read`, `activity.read`, `activity.statistics`, `duplicate.read`

> On Immich versions prior to 1.138.0, select **All** permissions.

## Usage

### stdio (Claude Desktop / Claude Code)

```bash
export IMMICH_BASE_URL=https://photos.example.com
export IMMICH_API_KEY=your-api-key
immich-mcp --transport stdio
```

**Claude Desktop config** (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "immich": {
      "command": "immich-mcp",
      "args": ["--transport", "stdio"],
      "env": {
        "IMMICH_BASE_URL": "https://photos.example.com",
        "IMMICH_API_KEY": "your-api-key"
      }
    }
  }
}
```

### HTTP (Docker / remote)

```bash
docker run -e IMMICH_BASE_URL=https://photos.example.com \
           -e IMMICH_API_KEY=your-api-key \
           -p 8000:8000 \
           ghcr.io/whitehara/immich-mcp:latest
```

Or build locally with `docker compose up`.

Default transport in Docker is `streamable-http` on port 8000.

## Tool Reference

Annotation columns: **R** = `readOnlyHint`, **D** = `destructiveHint`, **I** = `idempotentHint`

Each tool also carries a human-readable `title` annotation used by MCP clients for display.

### Health

| Tool | Description | R | D | I |
|------|-------------|:-:|:-:|:-:|
| `immich_ping` | Verify connectivity, returns server version | ✓ | | ✓ |
| `immich_capabilities` | List supported server features | ✓ | | ✓ |

### User

| Tool | Description | R | D | I |
|------|-------------|:-:|:-:|:-:|
| `immich_user_me` | Get the authenticated user's profile (name, email, quota, role) | ✓ | | ✓ |

### Assets

| Tool | Description | R | D | I |
|------|-------------|:-:|:-:|:-:|
| `immich_assets_list` | List assets with filters (favorite, archived, trashed, type) | ✓ | | ✓ |
| `immich_assets_get` | Get full metadata for a single asset | ✓ | | ✓ |
| `immich_assets_view` | Get thumbnail, original, and web UI URLs for an asset | ✓ | | ✓ |
| `immich_assets_upload` | Upload an asset from a local file path or URL | | | |
| `immich_assets_update` | Update favorite, archived, description, rating | | | ✓ |
| `immich_assets_bulk_update` | Bulk update multiple assets (dry_run supported) | | | ✓ |
| `immich_assets_delete` | Delete assets, optionally permanently (dry_run supported) | | ✓ | ✓ |
| `immich_assets_statistics` | Get counts by asset type | ✓ | | ✓ |

### Search

| Tool | Description | R | D | I |
|------|-------------|:-:|:-:|:-:|
| `immich_search_metadata` | Filter by date, type, location, camera, person, filename | ✓ | | |
| `immich_search_smart` | Semantic/CLIP search with natural language queries | ✓ | | |
| `immich_search_explore` | Discover popular places, people, and things | ✓ | | ✓ |

### Albums

| Tool | Description | R | D | I |
|------|-------------|:-:|:-:|:-:|
| `immich_albums_list` | List all albums | ✓ | | ✓ |
| `immich_albums_get` | Get album details and assets | ✓ | | ✓ |
| `immich_albums_create` | Create a new album | | | |
| `immich_albums_update` | Update album name, description, or cover | | | ✓ |
| `immich_albums_delete` | Delete an album (assets are not deleted) | | ✓ | ✓ |
| `immich_albums_add_assets` | Add assets to an album | | | ✓ |
| `immich_albums_remove_assets` | Remove assets from an album | | | ✓ |

### People

| Tool | Description | R | D | I |
|------|-------------|:-:|:-:|:-:|
| `immich_people_list` | List recognized people | ✓ | | ✓ |
| `immich_people_get` | Get person details | ✓ | | ✓ |
| `immich_people_update` | Update name or visibility | | | ✓ |
| `immich_people_merge` | Merge two face clusters | | ✓ | |
| `immich_people_statistics` | Get asset count for a person | ✓ | | ✓ |

### Tags

| Tool | Description | R | D | I |
|------|-------------|:-:|:-:|:-:|
| `immich_tags_list` | List all tags | ✓ | | ✓ |
| `immich_tags_get` | Get a tag by ID | ✓ | | ✓ |
| `immich_tags_create` | Create a tag (use `/` for nested tags) | | | |
| `immich_tags_update` | Update tag name or color | | | ✓ |
| `immich_tags_delete` | Delete a tag | | ✓ | ✓ |

### Shared Links

| Tool | Description | R | D | I |
|------|-------------|:-:|:-:|:-:|
| `immich_shared_links_list` | List all shared links | ✓ | | ✓ |
| `immich_shared_links_get` | Get shared link details | ✓ | | ✓ |
| `immich_shared_links_create` | Create a shareable URL | | | |
| `immich_shared_links_update` | Update expiry, password, permissions | | | ✓ |
| `immich_shared_links_remove` | Revoke a shared link | | ✓ | ✓ |

### Activities

| Tool | Description | R | D | I |
|------|-------------|:-:|:-:|:-:|
| `immich_activities_list` | List comments and likes | ✓ | | ✓ |
| `immich_activities_create` | Add a comment or like | | | |
| `immich_activities_delete` | Delete an activity | | ✓ | ✓ |
| `immich_activities_statistics` | Get comment count | ✓ | | ✓ |

### Duplicates

| Tool | Description | R | D | I |
|------|-------------|:-:|:-:|:-:|
| `immich_duplicates_list` | List duplicate groups with analysis (format score, resolution, protection status). Paginated (`page`/`page_size`, default 50 groups/page). Results are served from an in-memory cache; first call after server start returns `cache_ready=false` while data loads — large libraries may take 20–30 minutes on first load. | ✓ | | ✓ |
| `immich_duplicates_delete` | Delete assets from duplicate groups (dry_run supported) | | ✓ | ✓ |
| `immich_duplicates_dismiss` | Dismiss duplicate groups without deleting files (dry_run supported) | | ✓ | ✓ |

#### Pagination

`immich_duplicates_list` returns paginated results to avoid oversized responses on large libraries:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `page` | `1` | Page number (1-based) |
| `page_size` | `50` | Groups per page (max 500) |

The response includes `total_groups`, `total_pages`, `page`, and `page_size` fields. Iterate `page=1..total_pages` to process all groups.

#### Duplicate Analysis Fields

`immich_duplicates_list` with `analyze=true` (default) returns per-group analysis:

| Field | Description |
|-------|-------------|
| `keep_id` | Recommended asset to retain (highest quality) |
| `safe_to_delete_ids` | Assets not favorited and not in any album |
| `protected_ids` | Assets that are favorited or in albums — require explicit user approval |
| `needs_review` | `true` when protected assets appear among delete candidates |

#### Quality Priority for `keep_id` (highest to lowest)

Live Photo > Format score > Resolution > File size

Favorites and album membership are tiebreakers only — they do not override a quality difference. A favorited JPEG will not be recommended over an unfavorited RAW; instead the JPEG is listed in `protected_ids` for user review.

#### Format Score (highest to lowest)

RAW/DNG > HEIC/HEIF > PNG/TIFF > JPEG > WebP > GIF

## Prompt Reference

Invoke prompts from your MCP client to start guided workflows.

### `immich/review_duplicates`

Step-by-step workflow for reviewing and safely resolving duplicate photos:
1. Fetch duplicate groups with analysis
2. Present summary: safe-to-delete count vs. protected assets needing review
3. For each group, choose an action:
   - **Delete**: keep the best asset, move the rest to trash (or permanently delete)
   - **Dismiss**: assets are intentionally kept as separate copies — remove the duplicate grouping without deleting files
4. Dry-run confirmation before execution

### `immich/organize_album`

Guided album creation workflow:
- Organize by date, event, person, or location
- Uses both metadata search and semantic (CLIP) search
- Checks for existing albums to avoid duplicates
- Confirms asset count before creating

### `immich/find_untagged`

Discover unorganized assets in the library:
- Identifies assets with no album, no description, or no recognized people
- Suggests descriptions from EXIF data
- Hands off to `immich/organize_album` for album creation

## Safety Model

All destructive tools (`delete`, `merge`, `remove`) carry `destructiveHint=true` in their MCP annotations, signalling to clients that human confirmation is required before execution. Additional safeguards:

- `dry_run=true` is the default on all delete operations — no changes occur without explicit opt-in
- Duplicate analysis places favorited and album-linked assets in `protected_ids`; they are never auto-deleted
- Prompts explicitly instruct the AI to present a summary and obtain user approval before any destructive action

## Development

```bash
# Install with dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Run a single test file
pytest tests/tools/test_assets.py -v

# Type check (optional)
pyright src/
```
