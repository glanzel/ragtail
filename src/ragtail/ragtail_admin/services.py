from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException, Request

from ..models import Locale, Menu, MenuItem, Page, Site, User
from ..page_types import cast_page, get_default_page_model, persist_page
from ..pages import create_page, repath_page_subtree
from ..routing import (
    get_default_locale,
    get_translation,
    normalize_path,
)
from ..sites import (
    clear_other_default_locales,
    compute_page_path,
    ensure_default_site,
    ensure_tree_root,
    get_default_site,
    get_site_default_locale,
    get_site_root_page,
    get_site_root_page_id,
    get_tree_root,
    is_page_descendant_of,
    is_tree_root,
    page_admin_title,
    set_site_root_page,
    sync_default_locale_from_site,
)

ADMIN_LOCALE_SESSION_KEY = "ragtail_admin_locale"


@dataclass(frozen=True)
class PageTreeNode:
    page: Page
    children: list[PageTreeNode]


@dataclass(frozen=True)
class Breadcrumb:
    title: str
    url: str | None


async def get_admin_locale(request: Request | None = None) -> Locale:
    if request is not None:
        language_code = request.session.get(ADMIN_LOCALE_SESSION_KEY)
        if language_code:
            locale = await Locale.objects.get_or_none(
                language_code=language_code,
                is_active=True,
            )
            if locale is not None:
                return locale
    locale = await get_default_locale()
    if locale is None:
        raise HTTPException(status_code=500, detail="No default locale configured")
    return locale


def set_admin_locale(request: Request, locale: Locale) -> None:
    request.session[ADMIN_LOCALE_SESSION_KEY] = locale.language_code


async def resolve_page_for_admin_locale(page: Page, admin_locale: Locale) -> Page:
    if page.locale_id == admin_locale.id or page.translation_key is None:
        return page
    translated = await get_translation(page, admin_locale.language_code)
    return translated or page


async def resolve_translated_parent(source_page: Page, target_locale: Locale) -> Page:
    if source_page.parent_id is None:
        return await ensure_tree_root(target_locale)
    parent = await Page.objects.get_or_none(id=source_page.parent_id)
    if parent is None or is_tree_root(parent):
        return await ensure_tree_root(target_locale)
    translated_parent = await get_translation(parent, target_locale.language_code)
    if translated_parent is not None:
        return translated_parent
    return await ensure_tree_root(target_locale)


async def get_locales_missing_translation(page: Page) -> list[Locale]:
    if page.id is None:
        return []
    missing = await get_missing_translations_by_page([page])
    return missing.get(page.id, [])


async def get_missing_translations_by_page(pages: list[Page]) -> dict[int, list[Locale]]:
    if not pages:
        return {}
    translation_keys = {page.translation_key for page in pages if page.translation_key}
    if not translation_keys:
        return {page.id: [] for page in pages if page.id is not None}

    locales = [locale for locale in await get_all_locales() if locale.is_active]
    siblings = await Page.objects.filter(translation_key__in=list(translation_keys)).all()
    by_key_and_locale: dict[tuple[str, int], Page] = {}
    for sibling in siblings:
        if sibling.translation_key is not None and sibling.locale_id is not None:
            by_key_and_locale[(sibling.translation_key, sibling.locale_id)] = sibling

    result: dict[int, list[Locale]] = {}
    for page in pages:
        if page.id is None or page.translation_key is None:
            result[page.id] = []
            continue
        missing = [
            locale
            for locale in locales
            if locale.id != page.locale_id
            and (page.translation_key, locale.id) not in by_key_and_locale
        ]
        result[page.id] = missing
    return result


async def get_explorer_content_root(locale: Locale) -> Page:
    """Return the page that anchors the public site tree in the explorer."""

    site = await get_default_site()
    if site is not None and site.root_page_id is not None:
        homepage = await Page.objects.get_or_none(id=site.root_page_id)
        if (
            homepage is not None
            and homepage.locale_id == locale.id
            and not is_tree_root(homepage)
        ):
            return homepage
    return await ensure_tree_root(locale)


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
    locale = await get_default_locale()
    if locale is None:
        raise HTTPException(status_code=500, detail="No default locale configured")
    return locale


async def build_page_tree(locale: Locale) -> list[PageTreeNode]:
    pages = (
        await Page.objects.filter(locale_id=locale.id)
        .exclude(content_type="tree_root")
        .order_by("depth", "sort_order", "title")
        .all()
    )
    nodes: dict[int, PageTreeNode] = {}
    roots: list[PageTreeNode] = []

    for page in pages:
        if page.id is None:
            continue
        nodes[page.id] = PageTreeNode(page=page, children=[])

    tree_root = await get_tree_root(locale)
    tree_root_id = tree_root.id if tree_root is not None else None
    content_root = await get_explorer_content_root(locale)
    content_root_id = content_root.id if content_root is not None else None

    for page in pages:
        if page.id is None:
            continue
        node = nodes[page.id]
        parent_id = page.parent_id
        if content_root_id is not None and page.id == content_root_id and not is_tree_root(content_root):
            roots.append(node)
        elif content_root_id == tree_root_id and parent_id == tree_root_id:
            roots.append(node)
        elif parent_id is not None and parent_id in nodes:
            nodes[parent_id].children.append(node)

    return roots


async def build_breadcrumbs(page: Page) -> list[Breadcrumb]:
    crumbs: list[Breadcrumb] = [Breadcrumb(title="Pages", url="/admin/pages/")]
    current = page
    chain: list[Page] = []

    while current is not None:
        if not is_tree_root(current):
            chain.append(current)
        if current.parent_id is None:
            break
        current = await Page.objects.get_or_none(id=current.parent_id)

    for ancestor in reversed(chain):
        crumbs.append(
            Breadcrumb(
                title=page_admin_title(ancestor),
                url=f"/admin/pages/{ancestor.id}/" if ancestor.id is not None else None,
            )
        )
    return crumbs


async def update_page(
    page: Page,
    *,
    title: str,
    slug: str,
    live: bool,
    show_in_menus: bool,
    seo_title: str | None,
    search_description: str | None,
    **extra_fields: object,
) -> Page:
    typed_page = await cast_page(page)
    parent = None
    if typed_page.parent_id is not None:
        parent = await Page.objects.get_or_none(id=typed_page.parent_id)
    locale = None
    if typed_page.locale_id is not None:
        locale = typed_page.locale
        if locale is None:
            locale = await Locale.objects.get_or_none(id=typed_page.locale_id)
    site_root_page_id = await get_site_root_page_id(locale) if locale is not None else None
    new_path = compute_page_path(
        parent,
        slug,
        site_root_page_id=site_root_page_id,
        page_id=typed_page.id,
    )

    typed_page.title = title
    typed_page.slug = slug.strip("/")
    typed_page.path = new_path
    typed_page.live = live
    typed_page.show_in_menus = show_in_menus
    typed_page.seo_title = seo_title
    typed_page.search_description = search_description
    for name, value in extra_fields.items():
        setattr(typed_page, name, value)
    await persist_page(typed_page)
    await repath_page_subtree(await Page.objects.get(id=typed_page.id))
    return await cast_page(await Page.objects.get(id=typed_page.id))


async def delete_page(page: Page, *, include_translations: bool = True) -> None:
    if page.id is None:
        return
    if is_tree_root(page):
        raise ValueError("The technical tree root cannot be deleted.")

    pages_to_delete: list[Page] = [page]
    if include_translations and page.translation_key:
        pages_to_delete = await Page.objects.filter(
            translation_key=page.translation_key,
        ).all()

    seen_ids: set[int] = set()
    for candidate in pages_to_delete:
        if candidate.id is None or candidate.id in seen_ids:
            continue
        seen_ids.add(candidate.id)
        if is_tree_root(candidate):
            raise ValueError("The technical tree root cannot be deleted.")
        for site in await Site.objects.filter(root_page_id=candidate.id).all():
            site.root_page_id = None
            await site.save()
        await candidate.delete()


async def count_translation_siblings(page: Page) -> int:
    if page.translation_key is None:
        return 0
    siblings = await Page.objects.filter(translation_key=page.translation_key).all()
    return sum(1 for sibling in siblings if sibling.id != page.id)


def can_delete_page(page: Page) -> tuple[bool, str | None]:
    if is_tree_root(page):
        return False, "The technical tree root cannot be deleted."
    return True, None


async def count_page_descendants(page: Page) -> int:
    if page.id is None:
        return 0
    total = 0
    children = await Page.objects.filter(parent_id=page.id).all()
    for child in children:
        total += 1 + await count_page_descendants(child)
    return total


async def is_site_root_page(page: Page) -> bool:
    if page.id is None:
        return False
    site = await get_default_site()
    return site is not None and site.root_page_id == page.id


async def delete_menu(menu: Menu) -> None:
    if menu.id is None:
        return
    await MenuItem.objects.filter(menu_id=menu.id).delete()
    await menu.delete()


async def can_delete_locale(locale: Locale) -> tuple[bool, str | None]:
    total = await Locale.objects.count()
    if total <= 1:
        return False, "Cannot delete the last locale."
    if locale.is_default:
        return False, "Set another locale as default before deleting this one."
    return True, None


async def delete_locale(locale: Locale) -> None:
    if locale.id is None:
        return
    site = await get_default_site()
    if site is not None and site.root_page_id is not None:
        root_page = await Page.objects.get_or_none(id=site.root_page_id)
        if root_page is not None and root_page.locale_id == locale.id:
            site.root_page_id = None
            await site.save()
    tree_root = await get_tree_root(locale)
    if tree_root is not None and tree_root.id is not None:
        top_level = await Page.objects.filter(parent_id=tree_root.id).all()
        for page in top_level:
            await delete_page(page, include_translations=False)
        await tree_root.delete()
    await locale.delete()


async def ensure_root_page(locale: Locale) -> Page:
    """Ensure tree root, site, and a homepage exist. Returns the locale homepage."""

    tree_root = await ensure_tree_root(locale)
    await ensure_default_site()
    existing_home = await get_site_root_page(locale)
    if existing_home is not None:
        return await cast_page(existing_home)
    home = await create_page(
        title="Home",
        slug="",
        locale=locale,
        parent=tree_root,
        live=True,
        show_in_menus=True,
        page_model=get_default_page_model(),
    )
    site = await get_default_site()
    default_locale = await get_site_default_locale(site) if site is not None else None
    if site is not None and (site.root_page_id is None or default_locale is None or default_locale.id == locale.id):
        await set_site_root_page(site, home)
    return await cast_page(home)


async def get_locale_or_404(locale_id: int) -> Locale:
    locale = await Locale.objects.get_or_none(id=locale_id)
    if locale is None:
        raise HTTPException(status_code=404, detail="Locale not found")
    return locale


async def create_locale(
    *,
    language_code: str,
    display_name: str,
    is_default: bool = False,
) -> Locale:
    if is_default:
        await clear_other_default_locales()
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
        await clear_other_default_locales(exclude_locale_id=locale.id)

    locale.display_name = display_name.strip()
    locale.is_default = is_default
    locale.is_active = is_active
    await locale.save()
    return locale


async def get_all_locales() -> list[Locale]:
    return await Locale.objects.order_by("sort_order", "language_code").all()


async def get_menus_for_locale(locale: Locale) -> list[Menu]:
    return await Menu.objects.filter(locale_id=locale.id).order_by("name").all()


async def get_menu_or_404(menu_id: int) -> Menu:
    menu = await Menu.objects.get_or_none(id=menu_id)
    if menu is None:
        raise HTTPException(status_code=404, detail="Menu not found")
    return menu


async def update_menu(
    menu: Menu,
    *,
    name: str,
    slug: str,
    is_active: bool,
) -> Menu:
    if not name.strip():
        raise ValueError("Name is required.")
    if not slug.strip():
        raise ValueError("Slug is required.")

    normalized_slug = slug.strip().lower()
    existing = await Menu.objects.filter(
        locale_id=menu.locale_id,
        slug=normalized_slug,
    ).first()
    if existing is not None and existing.id != menu.id:
        raise ValueError("A menu with this slug already exists for this locale.")

    menu.name = name.strip()
    menu.slug = normalized_slug
    menu.is_active = is_active
    await menu.save()
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


async def get_all_users() -> list[User]:
    return await User.objects.order_by("username").all()


async def get_user_or_404(user_id: int) -> User:
    user = await User.objects.get_or_none(id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


async def get_user_by_email(email: str) -> User | None:
    from ..auth import normalize_email

    return await User.objects.get_or_none(email=normalize_email(email))


async def count_active_staff_users(*, exclude_user_id: int | None = None) -> int:
    query = User.objects.filter(is_active=True, is_staff=True)
    if exclude_user_id is not None:
        query = query.exclude(id=exclude_user_id)
    return await query.count()


async def can_delete_user(*, target: User, actor: User) -> tuple[bool, str | None]:
    if target.id == actor.id:
        return False, "You cannot delete your own account."
    if target.is_active and target.is_staff:
        remaining = await count_active_staff_users(exclude_user_id=target.id)
        if remaining == 0:
            return False, "Cannot delete the last active staff user."
    return True, None


async def get_all_sites() -> list[Site]:
    return await Site.objects.order_by("hostname", "port").all()


async def get_site_or_404(site_id: int) -> Site:
    site = await Site.objects.get_or_none(id=site_id)
    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")
    return site


async def get_pages_for_site_root_choice(site: Site) -> list[Page]:
    default_locale = await get_site_default_locale(site)
    if default_locale is None:
        default_locale = await get_default_locale()
    if default_locale is None:
        return []
    return await _pages_for_locale_tree(default_locale)


async def _pages_for_locale_tree(locale: Locale) -> list[Page]:
    tree_root = await get_tree_root(locale)
    if tree_root is None:
        return []
    pages = await Page.objects.filter(locale_id=locale.id).order_by("path", "title").all()
    return [
        page
        for page in pages
        if not is_tree_root(page)
        and page.parent_id is not None
        and await is_page_descendant_of(page, tree_root)
    ]


async def get_explorer_root_listing(locale: Locale) -> tuple[Page, list[Page]]:
    content_root = await get_explorer_content_root(locale)
    children = await get_child_pages(content_root)
    return content_root, children


async def update_site(
    site: Site,
    *,
    hostname: str,
    port: int,
    site_name: str | None,
    root_page_id: int | None,
    is_default_site: bool,
    prefix_default_language: bool,
) -> Site:
    if not hostname.strip():
        raise ValueError("Hostname is required.")
    if port < 1 or port > 65535:
        raise ValueError("Port must be between 1 and 65535.")

    default_locale = await get_site_default_locale(site)
    if root_page_id is not None:
        page = await Page.objects.get_or_none(id=root_page_id)
        if page is None:
            raise ValueError("Root page not found.")
        if (
            site.root_page_id is not None
            and default_locale is not None
            and page.locale_id != default_locale.id
        ):
            raise ValueError("Root page must belong to the site's default locale.")
        if is_tree_root(page) or page.parent_id is None:
            raise ValueError("The technical tree root cannot be the site homepage.")

    if is_default_site:
        others = await Site.objects.filter(is_default_site=True).all()
        for other in others:
            if other.id != site.id:
                other.is_default_site = False
                await other.save()

    site.hostname = hostname.strip()
    site.port = port
    site.site_name = site_name.strip() if site_name and site_name.strip() else None
    site.is_default_site = is_default_site
    site.prefix_default_language = prefix_default_language
    site.root_page_id = root_page_id
    await site.save()

    if root_page_id is not None:
        root_page = await Page.objects.get_or_none(id=root_page_id)
        if root_page is None:
            raise ValueError("Root page not found.")
        await set_site_root_page(site, root_page)
    return site


async def validate_user_update(
    *,
    target: User,
    actor: User,
    is_active: bool,
    is_staff: bool,
) -> str | None:
    if target.id != actor.id:
        return None
    if not is_active:
        return "You cannot deactivate your own account."
    if not is_staff:
        return "You cannot remove your own staff access."
    return None

