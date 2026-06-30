from __future__ import annotations

import re
from pathlib import Path
from typing import Any, get_args, get_origin

from pydantic.fields import FieldInfo

from .models import Image, ImageFieldInfo, Rendition


def is_image_field(field_info: FieldInfo) -> bool:
    if any(isinstance(item, ImageFieldInfo) for item in field_info.metadata):
        return True
    return _annotation_is_image(field_info.annotation)


def _annotation_is_image(annotation: Any) -> bool:
    if annotation is Image:
        return True
    origin = get_origin(annotation)
    if origin is not None:
        return any(arg is Image for arg in get_args(annotation))
    return False


def image_field_renditions(field_info: FieldInfo) -> tuple[str, ...]:
    for item in field_info.metadata:
        if isinstance(item, ImageFieldInfo):
            return item.default_renditions
    return ()


def serialize_image_field_value(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, Image):
        return value.id
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


async def resolve_image_field_value(value: Any) -> Image | None:
    if value is None:
        return None
    if isinstance(value, Image):
        if value.id is not None and value.file:
            return value
        if value.id is not None:
            return await Image.objects.get_or_none(id=value.id)
        return value
    if isinstance(value, dict):
        image_id = value.get("id")
        if image_id is not None:
            return await Image.objects.get_or_none(id=image_id)
        return None
    image_id = serialize_image_field_value(value)
    if image_id is None:
        return None
    return await Image.objects.get_or_none(id=image_id)


def image_field_names(model_cls: type) -> list[str]:
    if model_cls is object:
        return []
    own_names = set(getattr(model_cls, "__annotations__", {}))
    names: list[str] = []
    for name in getattr(model_cls, "model_fields", {}):
        if name not in own_names:
            continue
        field_info = model_cls.model_fields[name]
        if is_image_field(field_info):
            names.append(name)
    return names


async def image_to_api_dict(image: Image | None, *, renditions: tuple[str, ...] = ()) -> dict[str, Any] | None:
    if image is None or image.id is None:
        return None
    payload: dict[str, Any] = {
        "id": image.id,
        "title": image.title,
        "url": image.url,
        "width": image.width,
        "height": image.height,
        "focal_point": {
            "x": image.focal_point_x,
            "y": image.focal_point_y,
        },
    }
    if renditions:
        rendition_payload: dict[str, Any] = {}
        for spec in renditions:
            try:
                rendition = await image.get_rendition(spec)
            except Exception:
                continue
            rendition_payload[spec] = rendition_to_api_dict(rendition)
        payload["renditions"] = rendition_payload
    return payload


def rendition_to_api_dict(rendition: Rendition) -> dict[str, Any]:
    return {
        "url": rendition.url,
        "width": rendition.width,
        "height": rendition.height,
        "filter_spec": rendition.filter_spec,
        "background_position_style": rendition.background_position_style,
    }


_SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_upload_filename(filename: str) -> str:
    cleaned = _SAFE_FILENAME_RE.sub("_", Path(filename).name).strip("._")
    return cleaned or "upload.jpg"
