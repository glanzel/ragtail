from __future__ import annotations

from oxyde import Field

from ragtail.images import Image, ImageField
from ragtail.images.templates import resolve_rendition
from ragtail.menus import get_menu_tree
from ragtail.models import Page
from ragtail.page_types import register_page_model
from ragtail.routing import RouteMatch
from ragtail.streamfield import (
    HtmlTextBlock,
    ImageBlock,
    MarkdownTextBlock,
    StreamField,
    StreamValue,
    render_stream_value_html,
)

from stream_blocks import CtaButtonBlock, HighlightBlock


@register_page_model
class ContentPage(Page):
    body: str | None = Field(default=None, db_type="TEXT")
    hero_image: Image | None = ImageField(
        default=None,
        renditions=("fill-1200x480", "width-400"),
    )
    content: StreamValue | None = StreamField(
        [
            MarkdownTextBlock(),
            HtmlTextBlock(),
            ImageBlock(renditions=("width-800",)),
            HighlightBlock(),
            CtaButtonBlock(),
        ],
        default=None,
    )

    async def get_context(self, request, route: RouteMatch) -> dict:
        _ = request
        menu_items = await get_menu_tree("main", language_code=route.locale.language_code)
        hero = await resolve_rendition(self.hero_image, "fill-1200x480")
        stream_html = await render_stream_value_html(self.content)
        return {"menu_items": menu_items, "hero": hero, "stream_html": stream_html}
