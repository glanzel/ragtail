# StreamField

Ragtail provides a Wagtail-inspired **StreamField** for flexible page content: an ordered list of typed blocks (Markdown, HTML, images, structured fields, and custom templates). Block data is stored as JSON in the page row's `page_data` column — no extra database migration is required when you add a StreamField to a page model.

## Basic usage

```python
from oxyde import Field
from ragtail import Page, register_page_model
from ragtail.streamfield import (
    HtmlTextBlock,
    ImageBlock,
    MarkdownTextBlock,
    StreamField,
    StreamValue,
    render_stream_value_html,
)

@register_page_model
class ContentPage(Page):
    content: StreamValue | None = StreamField(
        [
            MarkdownTextBlock(),
            HtmlTextBlock(),
            ImageBlock(renditions=("width-800",)),
        ],
        default=None,
    )

    async def get_context(self, request, route):
        stream_html = await render_stream_value_html(self.content)
        return {"stream_html": stream_html}
```

In a PyJSX template, output the rendered HTML with `HTMLDontEscape`:

```python
from pyjsx.jsx import HTMLDontEscape

<div class="prose">{HTMLDontEscape(context["stream_html"])}</div>
```

See `examples/demo/pages.py` and `examples/demo/site_templates/content_page.px`.

## Storage format

Each block is stored as a JSON object in `page_data`:

```json
[
  {"id": "a1b2c3d4", "type": "markdown_text", "value": "## Hello\n\nWorld"},
  {"id": "e5f6g7h8", "type": "html_text", "value": "<p>Rich HTML</p>"},
  {"id": "i9j0k1l2", "type": "image", "value": 42}
]
```

- `type` matches the block's `name` (e.g. `markdown_text`, `cta_button`)
- `value` is a string, integer (image ID), or object (struct blocks)

`cast_page()` resolves image IDs to `Image` instances where applicable. The admin editor serialises blocks into a hidden JSON field on save.

## Built-in block types

| Block | `block_kind` | Stored value | Admin widget |
|-------|--------------|--------------|--------------|
| `MarkdownTextBlock` | `markdown` | Markdown string | Textarea |
| `HtmlTextBlock` | `html` | Sanitised HTML | TipTap visual editor + HTML code toggle |
| `ImageBlock` | `image` | Image ID (int) | Image chooser |
| `CharBlock` | `char` | Plain text | Single-line input |
| `URLBlock` | `url` | URL string | URL input (auto-prefixes `https://`) |
| `StructBlock` | `struct` | Object `{field: value}` | One input per child field |

### Markdown

Rendered on the public site via the same pipeline as the page `body` field (`markdown-it` + bleach).

### HTML

Edited in the admin with **TipTap** (visual mode) or a raw **HTML code** tab. Stored HTML is sanitised with bleach before save.

### Image

Uses the image library chooser. Optional `renditions` on `ImageBlock` control which sizes are generated for the public site and API.

```python
ImageBlock(renditions=("width-800", "fill-1200x480"))
```

## Field blocks

### CharBlock

```python
from ragtail.streamfield import CharBlock

CharBlock(name="caption", label="Caption")
```

Without a template, values render as a `<p>` on the public site.

### URLBlock

```python
from ragtail.streamfield import URLBlock

URLBlock(name="link", label="Link")
```

Relative paths (`/about/`) and absolute URLs are accepted. Bare domains are normalised to `https://…`.

## Custom blocks with templates

Subclass `CharBlock` (or another block) and set a `template` with `{value}` placeholders:

```python
from ragtail.streamfield import CharBlock

class HighlightBlock(CharBlock):
    template = '<mark class="bg-yellow-200 px-1">{value}</mark>'

    def __init__(self) -> None:
        super().__init__(name="highlight", label="Highlight")
```

Placeholder values are HTML-escaped when rendered.

## StructBlock (multiple fields + template)

Combine child blocks and render through an HTML template with `{field_name}` placeholders:

```python
from ragtail.streamfield import CharBlock, StructBlock, URLBlock

class CtaButtonBlock(StructBlock):
    def __init__(self) -> None:
        super().__init__(
            name="cta_button",
            label="Button / Link",
            fields={
                "label": CharBlock(name="label", label="Button text"),
                "url": URLBlock(name="url", label="Link URL"),
            },
            template=(
                '<a href="{url}" class="btn">{label}</a>'
            ),
        )
```

Register the block in your `StreamField` list like any built-in type. Full demo examples live in `examples/demo/stream_blocks.py`.

## Subclassing `Block`

All block types inherit from `ragtail.streamfield.Block`. You can subclass `Block` directly for full control:

```python
from ragtail.streamfield import Block

class QuoteBlock(Block):
    block_kind = "char"
    template = "<blockquote><p>{value}</p></blockquote>"

    def __init__(self) -> None:
        super().__init__(name="quote", label="Quote")
```

Override `prepare_value()` or `render_value()` on the base class when you need custom validation or output.

## Admin

StreamField properties appear automatically in the page editor when declared on a registered page model. Editors can:

- add blocks from the buttons below the stream area
- reorder blocks (Up / Down)
- remove blocks

The streamfield script (`streamfield.js`) is loaded when the page type includes a StreamField. HTML blocks load TipTap from the same bundle family as the main rich text editor.

Fields named `body` still use the separate page-level TipTap widget; stream Markdown blocks use a plain textarea.

## Public site rendering

### Render all blocks to HTML

```python
from ragtail.streamfield import render_stream_value_html

html = await render_stream_value_html(page.content)
```

Pass `block_definitions` if the `StreamValue` was loaded without definitions attached.

### Render a single block

```python
from ragtail.streamfield import render_stream_block_html

fragment = await render_stream_block_html(
    "markdown_text",
    "## Title",
    block_definitions=content_field_blocks,
)
```

### Custom per-block rendering in templates

Iterate `page.content.blocks` and branch on `block.type` instead of using `render_stream_value_html()` if you need full layout control.

## JSON API

`GET /api/cms/pages/{path}` includes StreamField data under `fields.<name>` when the page type defines extra fields. Image blocks include rendition metadata when configured on `ImageBlock`.

## Limitations (current iteration)

- Flat blocks only — no nested StreamBlocks inside StreamBlocks
- StructBlock child fields are `CharBlock` and `URLBlock` in the admin (extensible in code, not yet pluggable in the UI)
- No block-level preview in the admin
- Documents, workflows, and permissions are not covered here
