from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from fastapi import HTTPException, Request

from ..models import Locale, Menu, MenuItem, Page, User
from ..page_types import cast_page, get_default_page_model, persist_page
from ..pages import create_page
from ..routing import get_default_locale, get_translation, join_page_path, normalize_path

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
    if page.locale_id == admin_locale.id:
        return page
    if page.translation_key is None:
        return page
    translated = await Page.objects.filter(
        translation_key=page.translation_key,
        locale_id=admin_locale.id,
    ).first()
    return translated or page


async def resolve_translated_parent(source_page: Page, target_locale: Locale) -> Page:
    if source_page.parent_id is None:
        return await ensure_root_page(target_locale)
    parent = await Page.objects.get_or_none(id=source_page.parent_id)
    if parent is None:
        return await ensure_root_page(target_locale)
    translated_parent = await get_translation(parent, target_locale.language_code)
    if translated_parent is not None:
        return translated_parent
    return await ensure_root_page(target_locale)


async def get_locales_missing_translation(page: Page) -> list[Locale]:
    if page.translation_key is None:
        return []
    locales = await get_all_locales()
    missing: list[Locale] = []
    for locale in locales:
        if not locale.is_active or locale.id == page.locale_id:
            continue
        exists = await Page.objects.filter(
            translation_key=page.translation_key,
            locale_id=locale.id,
        ).first()
        if exists is None:
            missing.append(locale)
    return missing


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
    locale = await get_default_locale()
    if locale is None:
        raise HTTPException(status_code=500, detail="No default locale configured")
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


async def build_breadcrumbs(page: Page) -> list[Breadcrumb]:
    crumbs: list[Breadcrumb] = [Breadcrumb(title="Pages", url="/admin/pages/")]
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
    page_model: type[Page] | None = None,
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
        page_model=page_model or get_default_page_model(),
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
    typed_page = await cast_page(page)
    parent = None
    if typed_page.parent_id is not None:
        parent = await Page.objects.get_or_none(id=typed_page.parent_id)
    parent_path = parent.path if parent is not None else "/"
    new_path = (
        "/"
        if typed_page.parent is None and not slug.strip("/")
        else join_page_path(parent_path, slug)
    )

    typed_page.title = title
    typed_page.slug = slug.strip("/")
    typed_page.path = new_path
    if hasattr(typed_page, "body"):
        typed_page.body = body
    typed_page.live = live
    typed_page.show_in_menus = show_in_menus
    typed_page.seo_title = seo_title
    typed_page.search_description = search_description
    await persist_page(typed_page)
    await _repath_descendants(await Page.objects.get(id=typed_page.id))
    return await cast_page(await Page.objects.get(id=typed_page.id))


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
