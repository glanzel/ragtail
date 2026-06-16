from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Protocol

from fastapi import Request
from fastapi.responses import HTMLResponse, Response

from ..routing import RouteMatch
from .registry import get_page_view

PageRenderer = Callable[[Request, RouteMatch], Response | Awaitable[Response]]


def content_type_to_component_name(content_type: str) -> str:
    """Map ``detail_page`` to ``detailPage`` for PyJSX component lookup."""
    parts = content_type.strip("_").split("_")
    if not parts or not parts[0]:
        return content_type
    head, *tail = parts
    return head.lower() + "".join(part.capitalize() for part in tail)


async def resolve_view_and_context(
    request: Request,
    route: RouteMatch,
) -> tuple[Any, dict[str, Any]]:
    view = get_page_view(route.page.content_type or "page")
    context = await view.get_context(request, route.page, route)
    return view, context


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
