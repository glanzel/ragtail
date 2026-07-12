from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from pydantic.fields import FieldInfo

from ..images.models import Image
from ..richtext import prepare_body_for_storage, sanitize_rendered_html
from .blocks import Block, block_by_name
from .value import StreamBlockData, StreamValue, new_block_id


@dataclass(frozen=True)
class StreamFieldInfo:
    """Marker metadata for StreamField on Page models."""

    blocks: tuple[Block, ...] = ()


_RAGTAIL_STREAM_KEY = "ragtail_stream_field"


def _stream_info_from_field(field_info: FieldInfo) -> StreamFieldInfo | None:
    extra = field_info.json_schema_extra or {}
    info = extra.get(_RAGTAIL_STREAM_KEY)
    return info if isinstance(info, StreamFieldInfo) else None


def StreamField(
    blocks: list[Block],
    *,
    default: Any = None,
    **kwargs: Any,
):
    from oxyde import Field

    stream_info = StreamFieldInfo(blocks=tuple(blocks))
    metadata = list(kwargs.pop("metadata", []))
    metadata.append(stream_info)
    extra = dict(kwargs.pop("json_schema_extra", {}) or {})
    extra[_RAGTAIL_STREAM_KEY] = stream_info
    return Field(default=default, metadata=metadata, json_schema_extra=extra, **kwargs)


def is_stream_field(field_info: FieldInfo) -> bool:
    return _stream_info_from_field(field_info) is not None


def stream_field_blocks(field_info: FieldInfo) -> tuple[Block, ...]:
    info = _stream_info_from_field(field_info)
    return info.blocks if info is not None else ()


def stream_field_names(model_cls: type) -> list[str]:
    if model_cls is object:
        return []
    own_names = set(getattr(model_cls, "__annotations__", {}))
    names: list[str] = []
    for name in getattr(model_cls, "model_fields", {}):
        if name not in own_names:
            continue
        field_info = model_cls.model_fields[name]
        if is_stream_field(field_info):
            names.append(name)
    return names


def _prepare_block_value(block_def: Block, value: Any) -> Any:
    if value is None:
        return None
    if block_def.block_kind == "markdown":
        return prepare_body_for_storage(str(value))
    if block_def.block_kind == "html":
        cleaned = str(value).strip()
        return sanitize_rendered_html(cleaned) if cleaned else None
    if block_def.block_kind == "image":
        if isinstance(value, Image):
            return value.id
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.strip().isdigit():
            return int(value.strip())
        return None
    if block_def.block_kind == "struct":
        return block_def.prepare_value(value)
    return block_def.prepare_value(value)


def _is_empty_block_value(block_def: Block, value: Any) -> bool:
    if value is None:
        return True
    if block_def.block_kind == "struct":
        return not isinstance(value, dict) or not value
    if block_def.block_kind == "image":
        return False
    return value == ""


def prepare_stream_value_for_storage(
    value: Any,
    *,
    block_definitions: tuple[Block, ...],
) -> list[dict[str, Any]] | None:
    stream_value = StreamValue.from_data(value, block_definitions=block_definitions)
    if stream_value is None or not stream_value.blocks:
        return None

    allowed = {block.name for block in block_definitions}
    prepared_blocks: list[dict[str, Any]] = []
    for block in stream_value.blocks:
        if block.type not in allowed:
            continue
        block_def = block_by_name(block_definitions, block.type)
        if block_def is None:
            continue
        prepared_value = _prepare_block_value(block_def, block.value)
        if _is_empty_block_value(block_def, prepared_value):
            continue
        prepared_blocks.append(
            {
                "id": block.id or new_block_id(),
                "type": block.type,
                "value": prepared_value,
            }
        )
    return prepared_blocks or None


def serialize_stream_field_value(
    value: Any,
    *,
    block_definitions: tuple[Block, ...] = (),
) -> list[dict[str, Any]] | None:
    if value is None:
        return None
    if isinstance(value, StreamValue):
        return value.to_data() or None
    if isinstance(value, list):
        return value or None
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return None
        return parsed if isinstance(parsed, list) else None
    return None


def resolve_stream_field_value(
    value: Any,
    *,
    block_definitions: tuple[Block, ...] = (),
) -> StreamValue | None:
    if value is None:
        return None
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return None
    return StreamValue.from_data(value, block_definitions=block_definitions)


async def stream_value_to_api_dict(
    value: StreamValue | None,
    *,
    block_definitions: tuple[Block, ...] = (),
) -> list[dict[str, Any]] | None:
    from ..images.fields import image_to_api_dict

    if value is None or not value.blocks:
        return None
    definitions = block_definitions or value.block_definitions
    payload: list[dict[str, Any]] = []
    for block in value.blocks:
        block_def = block_by_name(definitions, block.type)
        entry: dict[str, Any] = {"id": block.id, "type": block.type, "value": block.value}
        if block_def is not None and block_def.block_kind == "image" and block.value is not None:
            image = await Image.objects.get_or_none(id=block.value)
            entry["value"] = await image_to_api_dict(image, renditions=block_def.renditions)
        payload.append(entry)
    return payload


def stream_blocks_for_admin(
    value: StreamValue | None,
    *,
    block_definitions: tuple[Block, ...],
) -> list[dict[str, Any]]:
    """Serialize blocks for the admin JSON widget, including image preview hints."""
    if value is None:
        return []
    definitions = block_definitions or value.block_definitions
    blocks: list[dict[str, Any]] = []
    for block in value.blocks:
        block_def = block_by_name(definitions, block.type)
        entry: dict[str, Any] = {
            "id": block.id,
            "type": block.type,
            "value": block.value if block.value is not None else "",
        }
        if block_def is not None:
            entry.update(block_def.admin_definition())
        blocks.append(entry)
    return blocks


def block_definitions_for_admin(block_definitions: tuple[Block, ...]) -> list[dict[str, Any]]:
    return [block.admin_definition() for block in block_definitions]
