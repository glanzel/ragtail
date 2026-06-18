from __future__ import annotations

from .models import Locale, Page, Site
from .routing import join_page_path, normalize_path

TREE_ROOT_CONTENT_TYPE = "tree_root"
TREE_ROOT_PATH = "/_tree_root_/"


def is_tree_root(page: Page) -> bool:
    return page.content_type == TREE_ROOT_CONTENT_TYPE or (
        page.parent_id is None and page.path == TREE_ROOT_PATH
    )


def page_admin_title(page: Page) -> str:
    if is_tree_root(page):
        return "Pages"
    return page.title


def compute_page_path(parent: Page | None, slug: str) -> str:
    """Build the stored public path for a page."""

    clean_slug = (slug or "").strip("/")
    if parent is None:
        return TREE_ROOT_PATH
    if is_tree_root(parent):
        if not clean_slug:
            return "/"
        return normalize_path(f"/{clean_slug}")
    return join_page_path(parent.path, slug)


async def get_tree_root(locale: Locale) -> Page | None:
    return await Page.objects.filter(
        locale_id=locale.id,
        parent_id__isnull=True,
        content_type=TREE_ROOT_CONTENT_TYPE,
    ).first()


async def ensure_tree_root(locale: Locale) -> Page:
    from .pages import create_page

    existing = await get_tree_root(locale)
    if existing is not None:
        return existing

    await migrate_legacy_roots(locale)
    existing = await get_tree_root(locale)
    if existing is not None:
        return existing

    return await create_page(
        title="",
        slug="_tree_root_",
        locale=locale,
        parent=None,
        live=False,
        show_in_menus=False,
        content_type=TREE_ROOT_CONTENT_TYPE,
        page_model=Page,
    )


async def migrate_legacy_roots(locale: Locale) -> None:
    """Move pre-Wagtail homepages under a technical tree root."""

    from .pages import create_page
    from .ragtail_admin.services import _repath_descendants

    legacy_roots = (
        await Page.objects.filter(locale_id=locale.id, parent_id__isnull=True)
        .exclude(content_type=TREE_ROOT_CONTENT_TYPE)
        .order_by("sort_order", "title")
        .all()
    )
    if not legacy_roots:
        return

    tree_root = await create_page(
        title="",
        slug="_tree_root_",
        locale=locale,
        parent=None,
        live=False,
        show_in_menus=False,
        content_type=TREE_ROOT_CONTENT_TYPE,
        page_model=Page,
    )
    site = await ensure_site(locale)
    for page in legacy_roots:
        if page.title.strip() in {"Root", "[Root]"} and not page.slug.strip("/"):
            page.title = "Home"
        page.parent_id = tree_root.id
        page.depth = tree_root.depth + 1
        await page.save()
        if site.root_page_id is None:
            site.root_page_id = page.id
            await site.save()
        await _repath_descendants(page)


async def get_site_for_locale(locale: Locale) -> Site | None:
    return await Site.objects.filter(locale_id=locale.id).first()


async def ensure_site(locale: Locale) -> Site:
    site = await get_site_for_locale(locale)
    if site is not None:
        return site
    hostname = "localhost" if locale.is_default else f"{locale.language_code}.localhost"
    return await Site.objects.create(
        hostname=hostname,
        port=80,
        locale_id=locale.id,
        is_default_site=locale.is_default,
    )


async def get_site_root_page(locale: Locale) -> Page | None:
    site = await get_site_for_locale(locale)
    if site is None or site.root_page_id is None:
        return None
    return await Page.objects.get_or_none(id=site.root_page_id)


async def set_site_root_page(site: Site, page: Page) -> Site:
    site.root_page_id = page.id
    await site.save()
    return site


async def get_site_for_page(page: Page) -> Site | None:
    if page.locale_id is None:
        return None
    return await get_site_for_locale(
        page.locale
        if page.locale is not None
        else await Locale.objects.get(id=page.locale_id)
    )


async def is_page_in_site_tree(page: Page, site: Site) -> bool:
    if site.root_page_id is None:
        return False
    if page.id == site.root_page_id:
        return True
    current_id = page.parent_id
    while current_id is not None:
        if current_id == site.root_page_id:
            return True
        parent = await Page.objects.get_or_none(id=current_id)
        if parent is None:
            return False
        current_id = parent.parent_id
    return False


async def is_page_publicly_routable(page: Page, locale: Locale) -> bool:
    if is_tree_root(page):
        return False
    site = await get_site_for_locale(locale)
    if site is None:
        return False
    return await is_page_in_site_tree(page, site)


async def get_top_level_pages(locale: Locale) -> list[Page]:
    tree_root = await get_tree_root(locale)
    if tree_root is None:
        return []
    return (
        await Page.objects.filter(parent_id=tree_root.id, locale_id=locale.id)
        .order_by("sort_order", "title")
        .all()
    )


async def ensure_site_setup(locale: Locale) -> tuple[Page, Site]:
    tree_root = await ensure_tree_root(locale)
    site = await ensure_site(locale)
    return tree_root, site


async def upgrade_all_locales() -> None:
    """Ensure technical tree roots, sites, and legacy homepage layouts exist."""

    locales = await Locale.objects.filter(is_active=True).order_by("sort_order", "language_code").all()
    for locale in locales:
        await ensure_site_setup(locale)
