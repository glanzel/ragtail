from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from fastapi import HTTPException

from ..models import Locale, Menu, MenuItem, Page
from ..pages import create_page
from ..routing import get_default_locale, join_page_path, normalize_path


@dataclass(frozen=True)
class PageTreeNode:
    page: Page
    children: list[PageTreeNode]


@dataclass(frozen=True)
class LocaleTreeSection:
    locale: Locale
    roots: list[PageTreeNode]


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
    filters: dict[str, object] = {"parent_id": page.id}
    if page.locale_id is not None:
        filters["locale_id"] = page.locale_id
    return (
        await Page.objects.filter(**filters)
        .order_by("sort_order", "title")
        .all()
    )


async def get_page_locale(page: Page) -> Locale:
    if page.locale_id is not None:
        locale = await Locale.objects.get_or_none(id=page.locale_id)
        if locale is not None:
            return locale
    if page.locale is not None:
        return page.locale
    locale = await get_admin_locale()
    return locale


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


async def build_all_locale_trees() -> list[LocaleTreeSection]:
    locales = await get_all_locales()
    sections: list[LocaleTreeSection] = []
    for locale in locales:
        if not locale.is_active:
            continue
        sections.append(
            LocaleTreeSection(locale=locale, roots=await build_page_tree(locale))
        )
    return sections


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


async def get_locale_or_404(locale_id: int) -> Locale:
    locale = await Locale.objects.get_or_none(id=locale_id)
    if locale is None:
        raise HTTPException(status_code=404, detail="Locale not found")
    return locale


async def _clear_other_default_locales(*, exclude_locale_id: int | None = None) -> None:
    defaults = await Locale.objects.filter(is_default=True).all()
    for other in defaults:
        if other.id == exclude_locale_id:
            continue
        other.is_default = False
        await other.save()


async def create_locale(
    *,
    language_code: str,
    display_name: str,
    is_default: bool = False,
) -> Locale:
    if is_default:
        await _clear_other_default_locales()
    return await Locale.objects.create(
        language_code=language_code,
        display_name=display_name,
        is_default=is_default,
        is_active=True,
    )


async def update_locale(
    locale: Locale,
    *,
    display_name: str,
    is_default: bool,
    is_active: bool,
) -> Locale:
    if not display_name.strip():
        raise ValueError("Display name is required.")

    if not is_active and locale.is_default:
        raise ValueError("Set another locale as default before deactivating this one.")

    if not is_default and locale.is_default:
        others = [
            other
            for other in await get_all_locales()
            if other.id != locale.id and other.is_active
        ]
        if not others:
            raise ValueError("At least one locale must be marked as default.")
        promoted = others[0]
        promoted.is_default = True
        await promoted.save()

    if is_default:
        await _clear_other_default_locales(exclude_locale_id=locale.id)

    locale.display_name = display_name.strip()
    locale.is_default = is_default
    locale.is_active = is_active
    await locale.save()
    return locale


def new_translation_key() -> str:
    return str(uuid4())


async def get_all_locales() -> list[Locale]:
    return await Locale.objects.order_by("sort_order", "language_code").all()


async def get_menus_for_locale(locale: Locale) -> list[Menu]:
    return await Menu.objects.filter(locale_id=locale.id).order_by("name").all()


async def get_menu_or_404(menu_id: int) -> Menu:
    menu = await Menu.objects.get_or_none(id=menu_id)
    if menu is None:
        raise HTTPException(status_code=404, detail="Menu not found")
    return menu


async def get_menu_items(menu: Menu) -> list[MenuItem]:
    items = (
        await MenuItem.objects.filter(menu_id=menu.id)
        .order_by("sort_order", "label")
        .all()
    )
    page_ids = [item.page_id for item in items if item.page_id is not None]
    if page_ids:
        pages = await Page.objects.filter(id__in=page_ids).all()
        pages_by_id = {page.id: page for page in pages}
        for item in items:
            if item.page_id in pages_by_id:
                item.page = pages_by_id[item.page_id]
    return items


async def get_pages_for_locale(locale: Locale) -> list[Page]:
    return await Page.objects.filter(locale_id=locale.id).order_by("path", "title").all()


async def get_menu_item_or_404(item_id: int) -> MenuItem:
    item = await MenuItem.objects.get_or_none(id=item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return item
