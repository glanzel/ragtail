from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Protocol

from .config import get_media_config


class StorageBackend(Protocol):
    async def save(self, path: str, data: bytes) -> str: ...

    async def open(self, path: str) -> bytes: ...

    async def delete(self, path: str) -> None: ...

    async def exists(self, path: str) -> bool: ...

    def url(self, path: str) -> str: ...

    def full_path(self, path: str) -> Path: ...


class LocalStorage:
    """Filesystem storage rooted at ``MEDIA_ROOT``."""

    def __init__(self, *, root: Path | None = None, url_prefix: str | None = None) -> None:
        config = get_media_config()
        self.root = Path(root) if root is not None else config.root
        self.url_prefix = url_prefix if url_prefix is not None else config.url

    def full_path(self, path: str) -> Path:
        return self.root / path

    async def save(self, path: str, data: bytes) -> str:
        target = self.full_path(path)
        await asyncio.to_thread(self._write_file, target, data)
        return path

    @staticmethod
    def _write_file(target: Path, data: bytes) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    async def open(self, path: str) -> bytes:
        return await asyncio.to_thread(self.full_path(path).read_bytes)

    async def delete(self, path: str) -> None:
        target = self.full_path(path)

        def _delete() -> None:
            if target.is_file():
                target.unlink()

        await asyncio.to_thread(_delete)

    async def exists(self, path: str) -> bool:
        return await asyncio.to_thread(self.full_path(path).is_file)

    def url(self, path: str) -> str:
        normalized = path.lstrip("/")
        prefix = self.url_prefix if self.url_prefix.endswith("/") else f"{self.url_prefix}/"
        return f"{prefix}{normalized}"


_storage: StorageBackend | None = None


def get_storage() -> StorageBackend:
    global _storage
    if _storage is None:
        _storage = LocalStorage()
    return _storage


def set_storage(storage: StorageBackend) -> None:
    global _storage
    _storage = storage


def reset_storage() -> None:
    global _storage
    _storage = None
