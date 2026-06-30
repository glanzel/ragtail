from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .fields import image_field_names, image_field_renditions
from .focal_point import FocalPoint
from .models import Image, Rendition


@dataclass(frozen=True)
class RenditionView:
    url: str
    width: int
    height: int
    alt: str
    filter_spec: str
    background_position_style: str
    focal_point: FocalPoint | None = None

    @classmethod
    def from_rendition(cls, rendition: Rendition, *, alt: str | None = None) -> RenditionView:
        return cls(
            url=rendition.url,
            width=rendition.width,
            height=rendition.height,
            alt=alt or rendition.alt,
            filter_spec=rendition.filter_spec,
            background_position_style=rendition.background_position_style,
            focal_point=rendition.focal_point,
        )


async def resolve_rendition(image: Image | None, filter_spec: str) -> RenditionView | None:
    if image is None or image.id is None:
        return None
    rendition = await image.get_rendition(filter_spec)
    return RenditionView.from_rendition(rendition, alt=image.title)


async def enrich_page_images(page: Any) -> dict[str, Any]:
    """Precompute renditions declared on ImageField metadata for template use."""
    model_cls = type(page)
    context: dict[str, Any] = {"_renditions": {}}
    for name in image_field_names(model_cls):
        image = getattr(page, name, None)
        if not isinstance(image, Image) or image.id is None:
            continue
        specs = image_field_renditions(model_cls.model_fields[name])
        if not specs:
            continue
        renditions: dict[str, RenditionView | None] = {}
        for spec in specs:
            resolved = await resolve_rendition(image, spec)
            renditions[spec] = resolved
            if resolved is not None:
                context["_renditions"][f"{image.id}:{spec}"] = resolved
        context[f"{name}_renditions"] = renditions
    return context


def render_image_tag(
    rendition: RenditionView | None,
    *,
    css_class: str = "",
    loading: str = "lazy",
) -> str:
    if rendition is None:
        return ""
    class_attr = f' class="{css_class}"' if css_class else ""
    loading_attr = f' loading="{loading}"' if loading else ""
    return (
        f'<img src="{rendition.url}" width="{rendition.width}" height="{rendition.height}" '
        f'alt="{_escape_attr(rendition.alt)}"{class_attr}{loading_attr} />'
    )


def _escape_attr(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
