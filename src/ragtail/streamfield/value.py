from __future__ import annotations

import json
import secrets
from dataclasses import dataclass, field
from typing import Any

from ..richtext import prepare_body_for_storage, render_body, sanitize_rendered_html
from .blocks import Block, block_by_name


def new_block_id() -> str:
    return secrets.token_hex(4)


@dataclass
class StreamBlockData:
    """A single block inside a StreamValue."""

    id: str
    type: str
    value: Any


@dataclass
class StreamValue:
    """Ordered list of stream blocks, comparable to Wagtail's StreamValue."""

    blocks: list[StreamBlockData] = field(default_factory=list)
    block_definitions: Any = field(default_factory=tuple, repr=False, compare=False)

    def to_data(self) -> list[dict[str, Any]]:
        return [{"id": block.id, "type": block.type, "value": block.value} for block in self.blocks]

    def to_json(self) -> str:
        return json.dumps(self.to_data(), ensure_ascii=False)

    @classmethod
    def from_data(
        cls,
        data: Any,
        *,
        block_definitions: tuple[Block, ...] = (),
    ) -> StreamValue | None:
        if data is None:
            return None
        if isinstance(data, cls):
            if block_definitions and not data.block_definitions:
                data.block_definitions = block_definitions
            return data
        if not isinstance(data, list):
            return None
        blocks: list[StreamBlockData] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            block_id = str(item.get("id") or new_block_id())
            block_type = str(item.get("type") or "")
            if not block_type:
                continue
            blocks.append(StreamBlockData(id=block_id, type=block_type, value=item.get("value")))
        return cls(blocks=blocks, block_definitions=block_definitions)

    def get_block_kind(self, block_type: str) -> str | None:
        definition = block_by_name(self.block_definitions, block_type)
        return definition.block_kind if definition is not None else None

    def render_html(self) -> str:
        """Render all blocks to a single HTML fragment (sync; image blocks need async render)."""
        parts: list[str] = []
        for block in self.blocks:
            kind = self.get_block_kind(block.type)
            if kind == "markdown" and block.value:
                parts.append(render_body(str(block.value)))
            elif kind == "html" and block.value:
                parts.append(sanitize_rendered_html(str(block.value)))
        return "\n".join(parts)
