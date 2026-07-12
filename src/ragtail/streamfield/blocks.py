from __future__ import annotations

import html
import re
from typing import Any, ClassVar

BlockKind = str

_URL_RE = re.compile(r"^https?://", re.IGNORECASE)


class Block:
    """Base stream block (Wagtail-style). Subclass for custom blocks with templates."""

    block_kind: ClassVar[str] = "block"
    template: ClassVar[str | None] = None

    def __init__(
        self,
        *,
        name: str,
        label: str,
        template: str | None = None,
        fields: dict[str, Block] | None = None,
        renditions: tuple[str, ...] = (),
    ) -> None:
        self.name = name
        self.label = label
        self._template = template
        self.fields = fields or {}
        self.renditions = renditions

    @property
    def effective_template(self) -> str | None:
        return self._template or self.template

    def admin_definition(self) -> dict[str, Any]:
        definition: dict[str, Any] = {
            "name": self.name,
            "label": self.label,
            "block_kind": self.block_kind,
        }
        if self.effective_template:
            definition["template"] = self.effective_template
        if self.fields:
            definition["fields"] = {
                field_name: field.admin_definition() for field_name, field in self.fields.items()
            }
        return definition

    def prepare_value(self, value: Any) -> Any:
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None

    def render_value(self, value: Any) -> str:
        if value is None:
            return ""
        template = self.effective_template
        if template and isinstance(value, dict):
            return render_block_template(template, value)
        if template:
            return render_block_template(template, {"value": value})
        return html.escape(str(value))


class CharBlock(Block):
    """Single-line text block."""

    block_kind: ClassVar[str] = "char"

    def __init__(self, *, name: str = "char", label: str = "Text") -> None:
        super().__init__(name=name, label=label)


class URLBlock(Block):
    """URL block with basic validation."""

    block_kind: ClassVar[str] = "url"

    def __init__(self, *, name: str = "url", label: str = "URL") -> None:
        super().__init__(name=name, label=label)

    def prepare_value(self, value: Any) -> Any:
        cleaned = super().prepare_value(value)
        if cleaned is None:
            return None
        if cleaned.startswith("/") or _URL_RE.match(cleaned):
            return cleaned
        return f"https://{cleaned}"


class MarkdownTextBlock(Block):
    """Markdown text block stored as markdown and rendered to HTML."""

    block_kind: ClassVar[str] = "markdown"

    def __init__(self, *, name: str = "markdown_text", label: str = "Markdown text") -> None:
        super().__init__(name=name, label=label)


class HtmlTextBlock(Block):
    """HTML text block stored as sanitized HTML."""

    block_kind: ClassVar[str] = "html"

    def __init__(self, *, name: str = "html_text", label: str = "HTML text") -> None:
        super().__init__(name=name, label=label)


class ImageBlock(Block):
    """Image block referencing an image from the media library."""

    block_kind: ClassVar[str] = "image"

    def __init__(
        self,
        *,
        name: str = "image",
        label: str = "Image",
        renditions: tuple[str, ...] = (),
    ) -> None:
        super().__init__(name=name, label=label, renditions=renditions)


class StructBlock(Block):
    """Group of child blocks rendered through a template with ``{field}`` placeholders."""

    block_kind: ClassVar[str] = "struct"

    def __init__(
        self,
        *,
        name: str,
        label: str,
        fields: dict[str, Block],
        template: str,
    ) -> None:
        if not fields:
            msg = "StructBlock requires at least one field"
            raise ValueError(msg)
        if not template.strip():
            msg = "StructBlock requires a template"
            raise ValueError(msg)
        super().__init__(name=name, label=label, template=template, fields=fields)

    def prepare_value(self, value: Any) -> dict[str, Any] | None:
        if not isinstance(value, dict):
            return None
        prepared: dict[str, Any] = {}
        for field_name, field_def in self.fields.items():
            if field_name not in value:
                continue
            field_value = field_def.prepare_value(value[field_name])
            if field_value is not None:
                prepared[field_name] = field_value
        return prepared or None

    def render_value(self, value: Any) -> str:
        if not isinstance(value, dict):
            return ""
        template = self.effective_template
        if not template:
            return ""
        return render_block_template(template, value)


def render_block_template(template: str, values: dict[str, Any]) -> str:
    """Fill ``{field}`` placeholders in a block template."""

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        return html.escape(str(values.get(key, "")))

    return re.sub(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}", replace, template)


def block_by_name(blocks: tuple[Block, ...], name: str) -> Block | None:
    for block in blocks:
        if block.name == name:
            return block
    return None
