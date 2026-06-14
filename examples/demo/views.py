from __future__ import annotations

from fastapi import Request

from oxytail.menus import get_menu_tree
from oxytail.models import Page
from oxytail.routing import RouteMatch
from oxytail.templates import PageView, register_page_view


@register_page_view
class SitePageView(PageView):
    content_type = "page"

    async def get_context(self, request: Request, page: Page, route: RouteMatch) -> dict:
        menu_items = await get_menu_tree("main", language_code=route.locale.language_code)
        return {"menu_items": menu_items}
