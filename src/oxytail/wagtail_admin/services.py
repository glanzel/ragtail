from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from fastapi import HTTPException

from ..models import Locale, Page
from ..pages import create_page
from ..routing import get_default_locale, join_page_path, normalize_path


@dataclass(frozen=True)
class PageTreeNode:
    page: Page
    children: list[PageTreeNode]


@dataclass(frozen=True)
class Breadcrumb:
    title: str
    url: str | None


async def get_admin_locale() -> Locale:
    locale = await get_default_locale()
    if locale is None:
        raise HTTPException(status_code=500, detail="No default locale configured")
    return locale


async def get_root_pages(locale: Locale) -> list[Page]:
    return (
        await Page.objects.filter(locale_id=locale.id, parent_id__isnull=True)
        .order_by("sort_order", "title")
        .all()
    )


async def get_page_or_404(page_id: int) -> Page:
    page = await Page.objects.get_or_none(id=page_id)
    if page is None:
        raise HTTPException(status_code=404, detail="Page not found")
    return page


async def get_child_pages(page: Page) -> list[Page]:
    return (
        await Page.objects.filter(parent_id=page.id)
        .order_by("sort_order", "title")
        .all()
    )


async def build_page_tree(locale: Locale) -> list[PageTreeNode]:
    pages = (
        await Page.objects.filter(locale_id=locale.id)
        .order_by("depth", "sort_order", "title")
        .all()
    )
    nodes: dict[int, PageTreeNode] = {}
    roots: list[PageTreeNode] = []

    for page in pages:
        if page.id is None:
            continue
        nodes[page.id] = PageTreeNode(page=page, children=[])

    for page in pages:
        if page.id is None:
            continue
        node = nodes[page.id]
        parent_id = page.parent_id
        if parent_id is not None and parent_id in nodes:
            nodes[parent_id].children.append(node)
        else:
            roots.append(node)

    return roots


async def build_breadcrumbs(page: Page) -> list[Breadcrumb]:
    crumbs: list[Breadcrumb] = [Breadcrumb(title="Root", url="/admin/pages/")]
    current = page
    chain: list[Page] = []

    while current is not None:
        chain.append(current)
        if current.parent_id is None:
            break
        current = await Page.objects.get_or_none(id=current.parent_id)

    for ancestor in reversed(chain):
        crumbs.append(
            Breadcrumb(
                title=ancestor.title,
                url=f"/admin/pages/{ancestor.id}/" if ancestor.id is not None else None,
            )
        )
    return crumbs


async def create_child_page(
    *,
    parent: Page | None,
    title: str,
    slug: str,
    locale: Locale,
    body: str | None = None,
    live: bool = False,
    show_in_menus: bool = False,
    seo_title: str | None = None,
    search_description: str | None = None,
) -> Page:
    return await create_page(
        title=title,
        slug=slug,
        locale=locale,
        parent=parent,
        live=live,
        show_in_menus=show_in_menus,
        body=body,
        seo_title=seo_title,
        search_description=search_description,
    )


async def update_page(
    page: Page,
    *,
    title: str,
    slug: str,
    body: str | None,
    live: bool,
    show_in_menus: bool,
    seo_title: str | None,
    search_description: str | None,
) -> Page:
    parent = None
    if page.parent_id is not None:
        parent = await Page.objects.get_or_none(id=page.parent_id)
    parent_path = parent.path if parent is not None else "/"
    new_path = (
        "/"
        if page.parent is None and not slug.strip("/")
        else join_page_path(parent_path, slug)
    )

    page.title = title
    page.slug = slug.strip("/")
    page.path = new_path
    page.body = body
    page.live = live
    page.show_in_menus = show_in_menus
    page.seo_title = seo_title
    page.search_description = search_description
    await page.save()
    await _repath_descendants(page)
    return page


async def _repath_descendants(page: Page) -> None:
    if page.id is None:
        return
    children = await Page.objects.filter(parent_id=page.id).all()
    for child in children:
        child.path = join_page_path(page.path, child.slug)
        await child.save()
        await _repath_descendants(child)


async def delete_page(page: Page) -> None:
    if page.id is None:
        return
    await page.delete()


async def ensure_root_page(locale: Locale) -> Page:
    roots = await get_root_pages(locale)
    if roots:
        return roots[0]
    return await create_page(title="Root", slug="", locale=locale, live=True, show_in_menus=True)


async def create_locale(
    *,
    language_code: str,
    display_name: str,
    is_default: bool = False,
) -> Locale:
    if is_default:
        defaults = await Locale.objects.filter(is_default=True).all()
        for locale in defaults:
            locale.is_default = False
            await locale.save()
    return await Locale.objects.create(
        language_code=language_code,
        display_name=display_name,
        is_default=is_default,
        is_active=True,
    )


def new_translation_key() -> str:
    return str(uuid4())
