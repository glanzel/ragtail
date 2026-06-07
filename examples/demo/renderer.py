from __future__ import annotations

import pyjsx.auto_setup  # noqa: F401
from fastapi import Request
from fastapi.responses import HTMLResponse

from oxytail.menus import get_menu_tree
from oxytail.routing import RouteMatch
from site_templates.page import SitePage


def create_site_renderer():
    async def render_page(_request: Request, route: RouteMatch) -> HTMLResponse:
        menu_items = await get_menu_tree("main", language_code=route.locale.language_code)
        return HTMLResponse(f"{SitePage(route=route, menu_items=menu_items)}")

    return render_page
