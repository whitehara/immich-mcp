import asyncio

import pytest
import immich_mcp.tools.duplicates as dup_mod
from immich_mcp.tools import duplicates
from immich_mcp.tools.duplicates import _analyze_group
from .conftest import get_annotations, get_fn


@pytest.fixture
def registered(mcp, patch_client):
    duplicates.register(mcp)
    return mcp, patch_client


@pytest.fixture(autouse=True)
def reset_cache():
    """Isolate cache state between tests."""
    dup_mod._cache = None
    dup_mod._cache_fetch_time = 0.0
    dup_mod._prefetch_task = None
    yield
    dup_mod._cache = None
    dup_mod._cache_fetch_time = 0.0
    dup_mod._prefetch_task = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_asset(
    id: str,
    mime_type: str = "image/jpeg",
    file_size: int = 1_000_000,
    width: int = 1000,
    height: int = 1000,
    is_favorite: bool = False,
    albums: list | None = None,
    is_trashed: bool = False,
    live_photo_video_id: str | None = None,
) -> dict:
    return {
        "id": id,
        "originalMimeType": mime_type,
        "fileSize": file_size,
        "exifInfo": {"exifImageWidth": width, "exifImageHeight": height},
        "isFavorite": is_favorite,
        "albums": albums if albums is not None else [],
        "isTrashed": is_trashed,
        "livePhotoVideoId": live_photo_video_id,
    }


# ---------------------------------------------------------------------------
# _analyze_group: format priority
# ---------------------------------------------------------------------------

def test_raw_beats_jpeg():
    assets = [
        make_asset("jpeg-id", mime_type="image/jpeg", file_size=2_000_000),
        make_asset("raw-id", mime_type="image/x-sony-arw", file_size=1_000_000),
    ]
    result = _analyze_group(assets)
    assert result["keep_id"] == "raw-id"
    assert "jpeg-id" in result["safe_to_delete_ids"]


def test_heic_beats_jpeg():
    assets = [
        make_asset("jpeg-id", mime_type="image/jpeg"),
        make_asset("heic-id", mime_type="image/heic"),
    ]
    result = _analyze_group(assets)
    assert result["keep_id"] == "heic-id"


def test_png_beats_jpeg():
    assets = [
        make_asset("png-id", mime_type="image/png"),
        make_asset("jpeg-id", mime_type="image/jpeg"),
    ]
    result = _analyze_group(assets)
    assert result["keep_id"] == "png-id"


# ---------------------------------------------------------------------------
# _analyze_group: size tiebreak within same format
# ---------------------------------------------------------------------------

def test_larger_file_wins_same_format():
    assets = [
        make_asset("small-id", mime_type="image/jpeg", file_size=500_000),
        make_asset("large-id", mime_type="image/jpeg", file_size=5_000_000),
    ]
    result = _analyze_group(assets)
    assert result["keep_id"] == "large-id"
    assert "small-id" in result["safe_to_delete_ids"]


def test_higher_resolution_wins():
    assets = [
        make_asset("lo-id", mime_type="image/jpeg", width=1000, height=1000),
        make_asset("hi-id", mime_type="image/jpeg", width=4000, height=3000),
    ]
    result = _analyze_group(assets)
    assert result["keep_id"] == "hi-id"


# ---------------------------------------------------------------------------
# _analyze_group: protection rules
# ---------------------------------------------------------------------------

def test_favorited_asset_is_protected():
    assets = [
        make_asset("fav-id", is_favorite=True),
        make_asset("plain-id"),
    ]
    result = _analyze_group(assets)
    assert result["keep_id"] == "fav-id"
    assert "plain-id" in result["safe_to_delete_ids"]
    assert result["needs_review"] is False


def test_favorited_is_never_in_safe_to_delete():
    assets = [
        make_asset("better-quality", mime_type="image/x-adobe-dng"),
        make_asset("fav-jpeg", mime_type="image/jpeg", is_favorite=True),
    ]
    result = _analyze_group(assets)
    # Even though RAW is higher quality, favorite must be protected
    assert "fav-jpeg" not in result["safe_to_delete_ids"]
    assert "fav-jpeg" in result["protected_ids"]
    assert result["needs_review"] is True


def test_album_member_is_protected():
    assets = [
        make_asset("album-id", albums=[{"id": "album-1"}]),
        make_asset("plain-id"),
    ]
    result = _analyze_group(assets)
    assert result["keep_id"] == "album-id"
    assert "plain-id" in result["safe_to_delete_ids"]
    assert result["needs_review"] is False


def test_album_member_among_delete_candidates_goes_to_protected():
    assets = [
        make_asset("raw-id", mime_type="image/x-adobe-dng"),
        make_asset("album-jpeg", mime_type="image/jpeg", albums=[{"id": "a1"}]),
    ]
    result = _analyze_group(assets)
    assert result["keep_id"] == "raw-id"
    assert "album-jpeg" in result["protected_ids"]
    assert result["needs_review"] is True


def test_needs_review_false_when_no_protected():
    assets = [
        make_asset("id1", mime_type="image/jpeg", file_size=2_000_000),
        make_asset("id2", mime_type="image/jpeg", file_size=1_000_000),
    ]
    result = _analyze_group(assets)
    assert result["needs_review"] is False
    assert result["protected_ids"] == []


# ---------------------------------------------------------------------------
# _analyze_group: Live Photo
# ---------------------------------------------------------------------------

def test_live_photo_beats_plain_jpeg():
    assets = [
        make_asset("plain-id", mime_type="image/jpeg"),
        make_asset("live-id", mime_type="image/jpeg", live_photo_video_id="video-uuid"),
    ]
    result = _analyze_group(assets)
    assert result["keep_id"] == "live-id"


# ---------------------------------------------------------------------------
# _analyze_group: multiple assets
# ---------------------------------------------------------------------------

def test_three_asset_group():
    assets = [
        make_asset("raw-id", mime_type="image/x-canon-cr2"),
        make_asset("heic-id", mime_type="image/heic"),
        make_asset("jpeg-id", mime_type="image/jpeg"),
    ]
    result = _analyze_group(assets)
    assert result["keep_id"] == "raw-id"
    assert len(result["safe_to_delete_ids"]) == 2
    assert "heic-id" in result["safe_to_delete_ids"]
    assert "jpeg-id" in result["safe_to_delete_ids"]


# ---------------------------------------------------------------------------
# immich.duplicates.list — prefetch / cache behaviour
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_returns_prefetching_when_cache_empty(registered):
    mcp, client = registered
    client.get.return_value = []

    result = await get_fn(mcp, "immich_duplicates_list")()

    assert result["cache_ready"] is False
    assert result["status"] == "prefetching"
    # Background task is created but client.get hasn't been awaited yet
    client.get.assert_not_called()


@pytest.mark.asyncio
async def test_list_populates_cache_in_background(registered):
    mcp, client = registered
    client.get.return_value = []

    # First call: prefetch starts
    await get_fn(mcp, "immich_duplicates_list")()
    # Yield control so the background task runs
    await asyncio.sleep(0)

    client.get.assert_called_once_with("/api/duplicates")
    assert dup_mod._cache == []


@pytest.mark.asyncio
async def test_list_returns_data_from_cache(registered):
    mcp, _ = registered
    dup_mod._cache = [
        {
            "duplicateId": "dup-1",
            "assets": [
                make_asset("a1", mime_type="image/jpeg"),
                make_asset("a2", mime_type="image/png"),
            ],
        }
    ]

    result = await get_fn(mcp, "immich_duplicates_list")()

    assert result["cache_ready"] is True
    assert result["total_groups"] == 1
    assert result["total_duplicates"] == 2
    assert result["page"] == 1
    assert result["page_size"] == 50
    assert result["total_pages"] == 1


@pytest.mark.asyncio
async def test_list_does_not_call_api_on_cache_hit(registered):
    mcp, client = registered
    dup_mod._cache = []

    await get_fn(mcp, "immich_duplicates_list")()

    client.get.assert_not_called()


@pytest.mark.asyncio
async def test_list_includes_analysis_by_default(registered):
    mcp, _ = registered
    dup_mod._cache = [
        {
            "duplicateId": "dup-1",
            "assets": [
                make_asset("jpeg-id", mime_type="image/jpeg"),
                make_asset("raw-id", mime_type="image/x-adobe-dng"),
            ],
        }
    ]

    result = await get_fn(mcp, "immich_duplicates_list")(analyze=True)

    group = result["groups"][0]
    assert "analysis" in group
    assert group["analysis"]["keep_id"] == "raw-id"


@pytest.mark.asyncio
async def test_list_skips_analysis_when_disabled(registered):
    mcp, _ = registered
    dup_mod._cache = [
        {"duplicateId": "dup-1", "assets": [make_asset("a1"), make_asset("a2")]}
    ]

    result = await get_fn(mcp, "immich_duplicates_list")(analyze=False)

    assert "analysis" not in result["groups"][0]


def test_list_is_readonly(registered):
    mcp, _ = registered
    ann = get_annotations(mcp, "immich_duplicates_list")
    assert ann.readOnlyHint is True
    assert ann.idempotentHint is True


@pytest.mark.asyncio
async def test_list_pagination(registered):
    mcp, _ = registered
    dup_mod._cache = [
        {"duplicateId": f"dup-{i}", "assets": [make_asset(f"a{i}")]}
        for i in range(7)
    ]

    result = await get_fn(mcp, "immich_duplicates_list")(page=2, page_size=3, analyze=False)

    assert result["total_groups"] == 7
    assert result["total_pages"] == 3
    assert result["page"] == 2
    assert result["page_size"] == 3
    assert len(result["groups"]) == 3
    assert result["groups"][0]["duplicate_id"] == "dup-3"


@pytest.mark.asyncio
async def test_list_pagination_last_page(registered):
    mcp, _ = registered
    dup_mod._cache = [
        {"duplicateId": f"dup-{i}", "assets": [make_asset(f"a{i}")]}
        for i in range(7)
    ]

    result = await get_fn(mcp, "immich_duplicates_list")(page=3, page_size=3, analyze=False)

    assert len(result["groups"]) == 1
    assert result["groups"][0]["duplicate_id"] == "dup-6"


# ---------------------------------------------------------------------------
# immich.duplicates.delete
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_delete_dry_run_default(registered):
    mcp, client = registered

    result = await get_fn(mcp, "immich_duplicates_delete")(["id1", "id2"])

    client.delete.assert_not_called()
    assert result["dry_run"] is True
    assert result["would_delete_count"] == 2
    assert result["permanent"] is False


@pytest.mark.asyncio
async def test_delete_dry_run_explicit_true(registered):
    mcp, client = registered

    result = await get_fn(mcp, "immich_duplicates_delete")(["id1"], dry_run=True)

    client.delete.assert_not_called()
    assert "message" in result


@pytest.mark.asyncio
async def test_delete_executes_with_dry_run_false(registered):
    mcp, client = registered

    result = await get_fn(mcp, "immich_duplicates_delete")(
        ["id1", "id2"], dry_run=False
    )

    client.delete.assert_called_once_with(
        "/api/assets", json={"ids": ["id1", "id2"], "force": False}
    )
    assert result["deleted_count"] == 2


@pytest.mark.asyncio
async def test_delete_permanent(registered):
    mcp, client = registered

    await get_fn(mcp, "immich_duplicates_delete")(["id1"], force=True, dry_run=False)

    _, kwargs = client.delete.call_args
    assert kwargs["json"]["force"] is True


def test_delete_is_destructive(registered):
    mcp, _ = registered
    ann = get_annotations(mcp, "immich_duplicates_delete")
    assert ann.destructiveHint is True
    assert ann.idempotentHint is True


# ---------------------------------------------------------------------------
# immich.duplicates.dismiss
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dismiss_dry_run_default(registered):
    mcp, client = registered

    result = await get_fn(mcp, "immich_duplicates_dismiss")(["dup-1", "dup-2"])

    client.delete.assert_not_called()
    assert result["dry_run"] is True
    assert result["would_dismiss_count"] == 2
    assert result["duplicate_ids"] == ["dup-1", "dup-2"]


@pytest.mark.asyncio
async def test_dismiss_dry_run_explicit_true(registered):
    mcp, client = registered

    result = await get_fn(mcp, "immich_duplicates_dismiss")(["dup-1"], dry_run=True)

    client.delete.assert_not_called()
    assert "message" in result


@pytest.mark.asyncio
async def test_dismiss_executes_with_dry_run_false(registered):
    mcp, client = registered

    result = await get_fn(mcp, "immich_duplicates_dismiss")(
        ["dup-1", "dup-2"], dry_run=False
    )

    client.delete.assert_called_once_with(
        "/api/duplicates", json={"ids": ["dup-1", "dup-2"]}
    )
    assert result["dismissed_count"] == 2
    assert result["duplicate_ids"] == ["dup-1", "dup-2"]


def test_dismiss_is_destructive(registered):
    mcp, _ = registered
    ann = get_annotations(mcp, "immich_duplicates_dismiss")
    assert ann.destructiveHint is True
    assert ann.idempotentHint is True
