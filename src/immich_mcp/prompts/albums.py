from mcp.server.fastmcp import FastMCP


def register(mcp: FastMCP) -> None:
    @mcp.prompt(name="immich/organize_album")
    def organize_album() -> str:
        return """
Organize the Immich photo library by creating and populating albums intelligently.

## Steps

1. Understand the user's organization goal. Common patterns:
   - By date: "Create albums by year/month"
   - By event: "Create an album for this trip / event"
   - By person: "Create an album for photos of [person name]"
   - By location: "Group photos by city/country"

2. Gather relevant assets:
   - Use `immich.search.metadata` for date, location, camera, or filename filters
   - Use `immich.search.smart` for semantic queries (e.g. "beach vacation", "birthday party")
   - Use `immich.people.list` + `immich.search.metadata` with `person_id` for person-based albums

3. Check for existing albums:
   - Call `immich.albums.list` to avoid creating duplicates
   - If a matching album exists, ask the user whether to add assets to it or create a new one

4. Create and populate:
   - Call `immich.albums.create` with a descriptive name and optional initial asset_ids
   - If the album already exists, use `immich.albums.add_assets`

5. Verify the result:
   - Call `immich.albums.get` to confirm the album contains the expected assets
   - Report: album name, asset count, date range of contents

## Naming Conventions

| Organization type | Suggested name format |
|------------------|-----------------------|
| By year | "2024" or "Photos 2024" |
| By month | "2024-03 March" |
| By event | "[Event Name] [Year]" e.g. "Tokyo Trip 2024" |
| By person | "[Person Name]" |
| By location | "[City, Country]" |

## Tips

- Prefer `immich.search.smart` for natural-language event descriptions
- For large result sets (>500 assets), break into multiple searches and merge IDs
- Always confirm the final asset count with the user before creating the album
- If assets belong to multiple categories, add them to all relevant albums
  (albums are non-exclusive in Immich)
"""
