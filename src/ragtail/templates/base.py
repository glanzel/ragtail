from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Protocol

from fastapi import Request
from fastapi.responses import HTMLResponse, Response

from ..page_types import cast_page, content_type_to_component_name
from ..routing import RouteMatch

PageRenderer = Callable[[Request, RouteMatch], Response | Awaitable[Response]]


async def resolve_page_and_context(
    request: Request,
    route: RouteMatch,
) -> tuple[Any, dict[str, Any]]:
    page = await cast_page(route.page)
    context = await page.get_context(request, route)
    return page, context


class TemplateEngineInterface(Protocol):
    async def serve(self, request: Request, route: RouteMatch) -> str: ...

    def as_renderer(self) -> PageRenderer: ...


class BaseTemplateEngine:
    """Shared helpers for concrete template engines."""

    async def serve(self, request: Request, route: RouteMatch) -> str:
        raise NotImplementedError

    def as_renderer(self) -> PageRenderer:
        async def render_page(request: Request, route: RouteMatch) -> HTMLResponse:
            html = await self.serve(request, route)
            return HTMLResponse(html)

        return render_page


__all__ = [
    "BaseTemplateEngine",
    "PageRenderer",
    "TemplateEngineInterface",
    "content_type_to_component_name",
    "resolve_page_and_context",
]
