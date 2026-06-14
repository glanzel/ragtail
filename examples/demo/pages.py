from __future__ import annotations

from oxyde import Field

from oxytail.menus import get_menu_tree
from oxytail.models import Page
from oxytail.page_types import register_page_model
from oxytail.routing import RouteMatch


@register_page_model
class ContentPage(Page):
    body: str | None = Field(default=None, db_type="TEXT")

    async def get_context(self, request, route: RouteMatch) -> dict:
        _ = request
        menu_items = await get_menu_tree("main", language_code=route.locale.language_code)
        return {"menu_items": menu_items}
