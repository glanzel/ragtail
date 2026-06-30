from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DEFAULT_MEDIA_ROOT = Path("media")
DEFAULT_MEDIA_URL = "/media/"


@dataclass
class MediaConfig:
    root: Path
    url: str = DEFAULT_MEDIA_URL

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        if not self.url.endswith("/"):
            self.url = f"{self.url}/"


_media_config: MediaConfig | None = None


def configure_media(*, root: str | Path, url: str = DEFAULT_MEDIA_URL) -> MediaConfig:
    global _media_config
    _media_config = MediaConfig(root=Path(root), url=url)
    return _media_config


def get_media_config() -> MediaConfig:
    if _media_config is None:
        return MediaConfig(root=DEFAULT_MEDIA_ROOT, url=DEFAULT_MEDIA_URL)
    return _media_config


def reset_media_config() -> None:
    global _media_config
    _media_config = None
