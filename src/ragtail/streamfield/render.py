from __future__ import annotations

import html

from ..images.templates import resolve_rendition
from ..richtext import render_body, sanitize_rendered_html
from .blocks import Block, block_by_name
from .value import StreamValue


async def render_stream_block_html(
    block_type: str,
    value: object,
    *,
    block_definitions: tuple[Block, ...],
) -> str:
    block_def = block_by_name(block_definitions, block_type)
    if block_def is None or value is None:
        return ""

    if block_def.block_kind == "markdown":
        return render_body(str(value))
    if block_def.block_kind == "html":
        return sanitize_rendered_html(str(value))
    if block_def.block_kind == "image":
        from ..images.models import Image

        image_id = value if isinstance(value, int) else None
        if image_id is None:
            return ""
        image = await Image.objects.get_or_none(id=image_id)
        if image is None:
            return ""
        rendition_spec = block_def.renditions[0] if block_def.renditions else None
        if rendition_spec:
            rendition = await resolve_rendition(image, rendition_spec)
            if rendition is not None:
                return (
                    f'<figure class="streamfield-image">'
                    f'<img src="{rendition.url}" width="{rendition.width}" '
                    f'height="{rendition.height}" alt="{image.title}" loading="lazy" />'
                    f"</figure>"
                )
        return (
            f'<figure class="streamfield-image">'
            f'<img src="{image.url}" width="{image.width}" '
            f'height="{image.height}" alt="{image.title}" loading="lazy" />'
            f"</figure>"
        )
    if block_def.effective_template:
        return block_def.render_value(value)
    if block_def.block_kind == "char":
        return f"<p>{html.escape(str(value))}</p>"
    if block_def.block_kind == "url":
        url = block_def.prepare_value(value)
        if not url:
            return ""
        return f'<a href="{html.escape(str(url), quote=True)}">{html.escape(str(value))}</a>'
    return ""


async def render_stream_value_html(
    value: StreamValue | None,
    *,
    block_definitions: tuple[Block, ...] | None = None,
) -> str:
    if value is None or not value.blocks:
        return ""
    definitions = block_definitions or value.block_definitions
    parts: list[str] = []
    for block in value.blocks:
        fragment = await render_stream_block_html(
            block.type,
            block.value,
            block_definitions=definitions,
        )
        if fragment:
            parts.append(fragment)
    return "\n".join(parts)
