from mcp.server.fastmcp import FastMCP


def register(mcp: FastMCP) -> None:
    @mcp.prompt(name="immich/find_untagged")
    def find_untagged() -> str:
        return """
Find and organize photos that lack tags, albums, or descriptions in the Immich library.

## Steps

1. Identify untagged/unorganized assets:
   - Call `immich.assets.statistics` to understand the library size
   - Use `immich.search.metadata` to find assets not belonging to albums
     (Note: Immich API does not directly filter by "no album" — use the explore endpoint
     and cross-reference with `immich.albums.list` to identify orphaned assets)
   - Use `immich.search.smart` with queries like "unlabeled", "no people", etc.
     to surface assets that may lack recognition data

2. Categorize what is missing:
   - No album membership → candidate for album organization (suggest `immich/organize_album`)
   - No description → offer to generate descriptions using visual content
   - No recognized people → may need manual face assignment via `immich.people.update`
   - Not favorited and no rating → ask user if they want to review

3. For assets without descriptions:
   - Retrieve the asset metadata with `immich.assets.get`
   - Use available EXIF data (date, location, camera) to suggest a description
   - Ask user to confirm or edit before applying via `immich.assets.update`

4. For assets not in any album:
   - Group by date (using `takenDate` from EXIF) or location (`city`, `country`)
   - Present grouping options to the user
   - Proceed with `immich/organize_album` workflow

5. Report a summary:
   - Count of assets with no album
   - Count of assets with no description
   - Count of assets with no recognized people
   - Recommended next steps

## Tips

- Process in batches of 50-100 assets to avoid overwhelming results
- Prioritize assets that are not archived and not trashed
- Favorited assets without albums are still "organized" by the user's intent — do not force them into albums
- Use `immich.tags.list` to understand existing tag taxonomy before creating new tags
"""
