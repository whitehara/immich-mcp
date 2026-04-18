from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class ImmichSettings(BaseSettings):
    base_url: str
    api_key: str
    timeout: float = 30.0
    max_retries: int = 3
    external_url: Optional[str] = None

    model_config = {"env_prefix": "IMMICH_"}


@lru_cache(maxsize=1)
def get_settings() -> ImmichSettings:
    return ImmichSettings()  # type: ignore[call-arg]
