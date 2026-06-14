from __future__ import annotations

from typing import Any
from uuid import uuid4

from .models import Locale, Page
from .page_types import cast_page, get_content_type, get_default_page_model, get_page_model
from .routing import join_page_path

_BASE_FIELD_NAMES = frozenset(
    {
        "id",
        "title",
        "slug",
        "path",
        "depth",
        "sort_order",
        "locale",
        "locale_id",
        "translation_key",
        "parent",
        "parent_id",
        "children",
        "content_type",
        "seo_title",
        "search_description",
        "live",
        "show_in_menus",
        "first_published_at",
        "last_published_at",
        "created_at",
        "updated_at",
    }
)


def _extra_field_values(page: Page, model: type[Page]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for name in model.model_fields:
        if name in _BASE_FIELD_NAMES:
            continue
        if hasattr(page, name):
            values[name] = getattr(page, name)
    return values


async def create_page(
    *,
    title: str,
    slug: str,
    locale: Locale,
    parent: Page | None = None,
    translation_key: str | None = None,
    live: bool = False,
    show_in_menus: bool = False,
    sort_order: int = 0,
    page_model: type[Page] | None = None,
    content_type: str | None = None,
    seo_title: str | None = None,
    search_description: str | None = None,
    **extra_fields: Any,
) -> Page:
    """Create a page with a normalized tree path and translation key."""

    model = page_model or get_default_page_model()
    resolved_content_type = content_type or get_content_type(model)

    parent_path = parent.path if parent is not None else "/"
    path = "/" if parent is None and not slug.strip("/") else join_page_path(parent_path, slug)
    depth = (parent.depth + 1) if parent is not None else 1

    stored = await Page.objects.create(
        title=title,
        slug=slug.strip("/"),
        path=path,
        depth=depth,
        sort_order=sort_order,
        locale_id=locale.id,
        parent_id=parent.id if parent is not None else None,
        translation_key=translation_key or str(uuid4()),
        live=live,
        show_in_menus=show_in_menus,
        content_type=resolved_content_type,
        seo_title=seo_title,
        search_description=search_description,
        **extra_fields,
    )
    return await cast_page(stored)


async def create_translation(
    source: Page,
    *,
    title: str,
    slug: str,
    locale: Locale,
    parent: Page | None = None,
    live: bool = False,
    show_in_menus: bool | None = None,
    **extra_fields: Any,
) -> Page:
    """Create a translated page that shares the source page's translation key."""

    typed_source = await cast_page(source)
    model = get_page_model(typed_source.content_type or "page")
    return await create_page(
        title=title,
        slug=slug,
        locale=locale,
        parent=parent,
        translation_key=typed_source.translation_key or str(uuid4()),
        live=live,
        show_in_menus=typed_source.show_in_menus if show_in_menus is None else show_in_menus,
        sort_order=typed_source.sort_order,
        page_model=model,
        seo_title=typed_source.seo_title,
        search_description=typed_source.search_description,
        **_extra_field_values(typed_source, model),
        **extra_fields,
    )
