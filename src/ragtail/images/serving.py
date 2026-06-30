from __future__ import annotations

import mimetypes
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response
from starlette.staticfiles import StaticFiles

from .config import get_media_config
from .storage import LocalStorage, get_storage


def create_media_router() -> APIRouter:
    router = APIRouter()

    @router.get("/{file_path:path}", include_in_schema=False)
    async def serve_media(file_path: str) -> Response:
        storage = get_storage()
        if not isinstance(storage, LocalStorage):
            raise HTTPException(status_code=501, detail="Media serving requires local storage")
        if ".." in Path(file_path).parts:
            raise HTTPException(status_code=404, detail="Not found")
        full_path = storage.full_path(file_path)
        if not full_path.is_file():
            raise HTTPException(status_code=404, detail="Not found")
        media_type, _ = mimetypes.guess_type(full_path.name)
        return FileResponse(full_path, media_type=media_type or "application/octet-stream")

    return router


def mount_media(app, *, prefix: str | None = None) -> None:
    media_url = prefix or get_media_config().url
    media_url = media_url.rstrip("/") or "/media"
    app.include_router(create_media_router(), prefix=media_url)


class MediaStaticFiles(StaticFiles):
    """StaticFiles wrapper for the configured media root."""

    def __init__(self) -> None:
        config = get_media_config()
        config.root.mkdir(parents=True, exist_ok=True)
        super().__init__(directory=str(config.root))
