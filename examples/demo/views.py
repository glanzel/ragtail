from __future__ import annotations

from fastapi import Request

from ragtail.menus import get_menu_tree
from ragtail.models import Page
from ragtail.routing import RouteMatch
from ragtail.templates import PageView, register_page_view


@register_page_view
class SitePageView(PageView):
    content_type = "page"

    async def get_context(self, request: Request, page: Page, route: RouteMatch) -> dict:
        menu_items = await get_menu_tree("main", language_code=route.locale.language_code)
        return {"menu_items": menu_items}
