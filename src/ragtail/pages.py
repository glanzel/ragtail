from __future__ import annotations

from uuid import uuid4

from .models import Locale, Page
from .routing import join_page_path


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
    content_type: str = "page",
    body: str | None = None,
    seo_title: str | None = None,
    search_description: str | None = None,
) -> Page:
    """Create a page with a normalized tree path and translation key."""

    parent_path = parent.path if parent is not None else "/"
    path = "/" if parent is None and not slug.strip("/") else join_page_path(parent_path, slug)
    depth = (parent.depth + 1) if parent is not None else 1

    return await Page.objects.create(
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
        content_type=content_type,
        body=body,
        seo_title=seo_title,
        search_description=search_description,
    )


async def create_translation(
    source: Page,
    *,
    title: str,
    slug: str,
    locale: Locale,
    parent: Page | None = None,
    live: bool = False,
    show_in_menus: bool | None = None,
    body: str | None = None,
) -> Page:
    """Create a translated page that shares the source page's translation key."""

    return await create_page(
        title=title,
        slug=slug,
        locale=locale,
        parent=parent,
        translation_key=source.translation_key or str(uuid4()),
        live=live,
        show_in_menus=source.show_in_menus if show_in_menus is None else show_in_menus,
        sort_order=source.sort_order,
        content_type=source.content_type,
        body=body,
    )
