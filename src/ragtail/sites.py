from __future__ import annotations

from .models import Locale, Page, Site
from .routing import get_translation, join_page_path, normalize_path

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


def compute_page_path(
    parent: Page | None,
    slug: str,
    *,
    site_root_page_id: int | None = None,
) -> str:
    """Build the stored public path for a page.

    Wagtail-like behaviour: the site homepage is served at ``/`` and its slug
    is omitted from descendant URLs (``/about/``, not ``/home/about/``).
    """

    clean_slug = (slug or "").strip("/")
    if parent is None:
        return TREE_ROOT_PATH
    if is_tree_root(parent):
        if not clean_slug:
            return "/"
        return normalize_path(f"/{clean_slug}")
    if site_root_page_id is not None and parent.id == site_root_page_id:
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


async def get_default_site() -> Site | None:
    site = await Site.objects.filter(is_default_site=True).first()
    if site is not None:
        return site
    return await Site.objects.order_by("id").first()


async def ensure_default_site() -> Site:
    site = await get_default_site()
    if site is not None:
        return site
    return await Site.objects.create(
        hostname="localhost",
        port=80,
        is_default_site=True,
    )


async def get_site_default_locale(site: Site) -> Locale | None:
    if site.root_page_id is None:
        return None
    root_page = await Page.objects.get_or_none(id=site.root_page_id)
    if root_page is None or root_page.locale_id is None:
        return None
    if root_page.locale is not None:
        return root_page.locale
    return await Locale.objects.get_or_none(id=root_page.locale_id)


async def get_homepage_for_locale(site: Site, locale: Locale) -> Page | None:
    """Return the homepage served at ``/`` for the given locale."""

    if site.root_page_id is None:
        return None

    root_page = await Page.objects.get_or_none(id=site.root_page_id)
    if root_page is None or is_tree_root(root_page):
        return None

    if root_page.locale_id == locale.id:
        return root_page

    translated = await get_translation(root_page, locale.language_code)
    if translated is not None and not is_tree_root(translated):
        return translated

    return root_page


async def sync_default_locale_from_site(site: Site) -> None:
    from .ragtail_admin.services import _clear_other_default_locales

    default_locale = await get_site_default_locale(site)
    if default_locale is None:
        return

    await _clear_other_default_locales(exclude_locale_id=default_locale.id)
    default_locale.is_default = True
    await default_locale.save()


async def get_site_root_page_id(locale: Locale) -> int | None:
    site = await get_default_site()
    if site is None:
        return None
    homepage = await get_homepage_for_locale(site, locale)
    return homepage.id if homepage is not None else None


async def get_site_root_page(locale: Locale) -> Page | None:
    site = await get_default_site()
    if site is None:
        return None
    return await get_homepage_for_locale(site, locale)


async def set_site_root_page(site: Site, page: Page) -> Site:
    site.root_page_id = page.id
    await site.save()
    if normalize_path(page.path) != "/":
        page.path = "/"
        await page.save()
    from .pages import repath_page_subtree

    await repath_page_subtree(page)
    await sync_default_locale_from_site(site)
    return site


async def is_page_descendant_of(page: Page, ancestor: Page) -> bool:
    if page.id == ancestor.id:
        return True
    current_id = page.parent_id
    while current_id is not None:
        if current_id == ancestor.id:
            return True
        parent = await Page.objects.get_or_none(id=current_id)
        if parent is None:
            return False
        current_id = parent.parent_id
    return False


async def is_page_in_site_tree(page: Page, homepage: Page) -> bool:
    if homepage.id is None:
        return False
    return await is_page_descendant_of(page, homepage)


async def is_page_publicly_routable(page: Page, locale: Locale) -> bool:
    if is_tree_root(page):
        return False
    site = await get_default_site()
    if site is None:
        return False
    homepage = await get_homepage_for_locale(site, locale)
    if homepage is None:
        return False
    return await is_page_in_site_tree(page, homepage)


async def get_top_level_pages(locale: Locale) -> list[Page]:
    tree_root = await get_tree_root(locale)
    if tree_root is None:
        return []
    return (
        await Page.objects.filter(parent_id=tree_root.id, locale_id=locale.id)
        .order_by("sort_order", "title")
        .all()
    )


async def ensure_site_homepage_paths() -> None:
    """Normalize the site homepage path and repath descendants when needed."""

    site = await get_default_site()
    if site is None or site.root_page_id is None:
        return
    homepage = await Page.objects.get_or_none(id=site.root_page_id)
    if homepage is None or is_tree_root(homepage):
        return
    await set_site_root_page(site, homepage)


async def upgrade_all_locales() -> None:
    """Ensure a default site and technical tree roots for active locales."""

    await ensure_default_site()
    locales = await Locale.objects.filter(is_active=True).order_by("sort_order", "language_code").all()
    for locale in locales:
        await ensure_tree_root(locale)
    await ensure_site_homepage_paths()
