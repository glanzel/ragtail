from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import Request

from ..images.fields import image_field_names
from ..images.templates import RenditionView, enrich_page_images, render_image_tag, resolve_rendition
from ..routing import RouteMatch
from .base import BaseTemplateEngine, resolve_page_and_context


class Jinja2Renderer(BaseTemplateEngine):
    """Render public pages with Jinja2 templates."""

    def __init__(
        self,
        template_dir: str | Path,
        *,
        register_image_tags: bool = True,
    ) -> None:
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
        self._register_image_tags = register_image_tags
        self._image_context: dict[str, Any] = {}
        if register_image_tags:
            self._register_jinja_image_helpers()

    def _register_jinja_image_helpers(self) -> None:
        environment = self._environment

        def rendition(image: Any, filter_spec: str) -> RenditionView | None:
            if image is None:
                return None
            image_id = getattr(image, "id", None)
            if image_id is None:
                return None
            bucket = self._image_context.get("_renditions", {})
            cached = bucket.get(f"{image_id}:{filter_spec}")
            if cached is not None:
                return cached
            field_name = getattr(image, "_ragtail_field_name", None)
            if field_name:
                field_bucket = self._image_context.get(f"{field_name}_renditions", {})
                return field_bucket.get(filter_spec)
            return None

        def ragtail_image(image: Any, filter_spec: str, css_class: str = "") -> str:
            from markupsafe import Markup

            resolved = rendition(image, filter_spec)
            return Markup(render_image_tag(resolved, css_class=css_class))

        environment.filters["rendition"] = rendition
        environment.globals["ragtail_image"] = ragtail_image

    async def serve(self, request: Request, route: RouteMatch) -> str:
        page, context = await resolve_page_and_context(request, route)
        image_context = await enrich_page_images(page)
        template_name = page.get_template_name(request, route)
        template_source = self._environment.loader.get_source(self._environment, template_name)[0]
        preloaded = await self._preload_template_renditions(page, template_source)
        merged_renditions = {
            **image_context.get("_renditions", {}),
            **preloaded.get("_renditions", {}),
        }
        image_context = {**image_context, **preloaded, "_renditions": merged_renditions}
        self._image_context = {**image_context, **context}
        template = self._environment.get_template(template_name)
        return template.render(
            page=page,
            route=route,
            request=request,
            **context,
            **image_context,
        )

    async def _preload_template_renditions(self, page: Any, template_source: str) -> dict[str, Any]:
        import re

        from ..images.models import Image

        requested_specs: set[str] = set()
        for match in re.finditer(
            r"(?:ragtail_image|rendition)\(\s*page\.(\w+)\s*,\s*[\"']([^\"']+)[\"']",
            template_source,
        ):
            requested_specs.add(match.group(2))

        preloaded: dict[str, RenditionView] = {}
        for name in image_field_names(type(page)):
            image = getattr(page, name, None)
            if not isinstance(image, Image) or image.id is None:
                continue
            for spec in requested_specs:
                resolved = await resolve_rendition(image, spec)
                if resolved is not None:
                    preloaded[f"{image.id}:{spec}"] = resolved

        if not preloaded:
            return {}
        return {"_renditions": preloaded}
