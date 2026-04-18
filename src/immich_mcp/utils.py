from .config import get_settings


def _web_base() -> str:
    s = get_settings()
    return (s.external_url or s.base_url).rstrip("/")


def _api_base() -> str:
    return get_settings().base_url.rstrip("/")


def asset_web_url(asset_id: str) -> str:
    return f"{_web_base()}/photos/{asset_id}"


def album_web_url(album_id: str) -> str:
    return f"{_web_base()}/albums/{album_id}"


def asset_thumbnail_url(asset_id: str) -> str:
    s = get_settings()
    return f"{_api_base()}/api/assets/{asset_id}/thumbnail?apiKey={s.api_key}"


def asset_original_url(asset_id: str) -> str:
    s = get_settings()
    return f"{_api_base()}/api/assets/{asset_id}/original?apiKey={s.api_key}"
