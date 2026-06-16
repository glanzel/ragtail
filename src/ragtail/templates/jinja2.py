from __future__ import annotations

from pathlib import Path

from fastapi import Request

from ..routing import RouteMatch
from .base import BaseTemplateEngine, resolve_page_and_context


class Jinja2Renderer(BaseTemplateEngine):
    """Render public pages with Jinja2 templates."""

    def __init__(self, template_dir: str | Path) -> None:
        try:
            from jinja2 import Environment, FileSystemLoader, select_autoescape
        except ImportError as exc:  # pragma: no cover - depends on optional extra
            raise ImportError(
                "Install the jinja extra to use Jinja2Renderer: uv add 'ragtail[jinja]'"
            ) from exc

        self._environment = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )

    async def serve(self, request: Request, route: RouteMatch) -> str:
        page, context = await resolve_page_and_context(request, route)
        template_name = page.get_template_name(request, route)
        template = self._environment.get_template(template_name)
        return template.render(
            page=page,
            route=route,
            request=request,
            **context,
        )
