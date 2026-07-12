from __future__ import annotations

import json

import pytest

from ragtail.streamfield import (
    CharBlock,
    HtmlTextBlock,
    MarkdownTextBlock,
    StreamBlockData,
    StreamField,
    StructBlock,
    StreamValue,
    URLBlock,
    prepare_stream_value_for_storage,
    render_block_template,
    render_stream_value_html,
    resolve_stream_field_value,
)
from ragtail.streamfield.blocks import block_by_name
from ragtail.streamfield.fields import _stream_info_from_field


def test_stream_field_factory_attaches_block_definitions() -> None:
    field = StreamField([MarkdownTextBlock(), HtmlTextBlock()])
    info = _stream_info_from_field(field)
    assert info is not None
    assert len(info.blocks) == 2


def test_prepare_stream_value_sanitizes_blocks() -> None:
    from ragtail.streamfield import ImageBlock

    blocks = (MarkdownTextBlock(), HtmlTextBlock(), ImageBlock())
    raw = [
        {"id": "a", "type": "markdown_text", "value": "## Hello\n\n<script>alert(1)</script>"},
        {"id": "b", "type": "html_text", "value": "<p>Hi</p><script>x</script>"},
        {"id": "c", "type": "image", "value": 42},
        {"id": "d", "type": "unknown", "value": "skip me"},
    ]
    prepared = prepare_stream_value_for_storage(raw, block_definitions=blocks)
    assert prepared is not None
    assert len(prepared) == 3
    assert "<script>" not in prepared[0]["value"]
    assert "<script>" not in prepared[1]["value"]
    assert prepared[2]["value"] == 42


def test_resolve_stream_field_value_roundtrip() -> None:
    blocks = (MarkdownTextBlock(),)
    data = [{"id": "x", "type": "markdown_text", "value": "Hello"}]
    value = resolve_stream_field_value(data, block_definitions=blocks)
    assert isinstance(value, StreamValue)
    assert value.blocks[0].value == "Hello"
    assert value.to_json() == json.dumps(data)


@pytest.mark.asyncio
async def test_render_stream_value_html_markdown_and_html() -> None:
    blocks = (MarkdownTextBlock(), HtmlTextBlock())
    value = StreamValue(
        blocks=[
            StreamBlockData(id="1", type="markdown_text", value="## Title"),
            StreamBlockData(id="2", type="html_text", value="<p><strong>HTML</strong></p>"),
        ],
        block_definitions=blocks,
    )
    html = await render_stream_value_html(value)
    assert "<h2>Title</h2>" in html
    assert "<strong>HTML</strong>" in html


def test_block_by_name() -> None:
    blocks = (MarkdownTextBlock(name="intro"), HtmlTextBlock())
    found = block_by_name(blocks, "intro")
    assert found is not None
    assert found.label == "Markdown text"


def test_char_block_with_template() -> None:
    class HighlightBlock(CharBlock):
        template = '<mark>{value}</mark>'

        def __init__(self) -> None:
            super().__init__(name="highlight", label="Highlight")

    block = HighlightBlock()
    assert block.render_value("Important") == '<mark>Important</mark>'


def test_url_block_normalizes_url() -> None:
    block = URLBlock()
    assert block.prepare_value("example.com") == "https://example.com"
    assert block.prepare_value("https://example.com") == "https://example.com"
    assert block.prepare_value("/about/") == "/about/"
    assert block.prepare_value("/de/kontakt") == "/de/kontakt"


def test_struct_block_template_rendering() -> None:
    block = StructBlock(
        name="cta",
        label="CTA",
        fields={"label": CharBlock(name="label", label="Text"), "url": URLBlock(name="url", label="URL")},
        template='<a href="{url}">{label}</a>',
    )
    html = block.render_value({"label": "Buy", "url": "https://shop.example"})
    assert html == '<a href="https://shop.example">Buy</a>'
    html = block.render_value({"label": "About", "url": "/about/"})
    assert html == '<a href="/about/">About</a>'


def test_render_block_template_escapes_values() -> None:
    rendered = render_block_template("<span>{value}</span>", {"value": '<script>"x"</script>'})
    assert "<script>" not in rendered
    assert "&lt;script&gt;" in rendered


@pytest.mark.asyncio
async def test_render_struct_block_on_page() -> None:
    block = StructBlock(
        name="cta",
        label="CTA",
        fields={"label": CharBlock(name="label", label="Text"), "url": URLBlock(name="url", label="URL")},
        template='<a href="{url}" class="btn">{label}</a>',
    )
    value = StreamValue(
        blocks=[StreamBlockData(id="1", type="cta", value={"label": "Go", "url": "https://example.com"})],
        block_definitions=(block,),
    )
    html = await render_stream_value_html(value)
    assert 'href="https://example.com"' in html
    assert ">Go</a>" in html
