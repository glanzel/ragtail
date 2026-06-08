from __future__ import annotations

import pyjsx.auto_setup  # noqa: F401
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse

from ..auth import authenticate_user
from ..menus import create_menu, create_menu_item
from ..models import Page, User
from .components.dashboard import DashboardPage
from .components.locales import LocaleAddPage, LocaleListPage
from .components.login import LoginPage
from .components.menus import MenuAddPage, MenuDetailPage, MenuListPage
from .components.pages import DeletePagePage, PageFormPage, PageListingPage
from .registry import get_page_form_fields, uses_richtext
from .render import html_response
from .services import (
    build_all_locale_trees,
    build_breadcrumbs,
    create_child_page,
    create_locale,
    delete_page,
    ensure_root_page,
    get_admin_locale,
    get_all_locales,
    get_child_pages,
    get_menu_item_or_404,
    get_menu_items,
    get_menu_or_404,
    get_menus_for_locale,
    get_page_locale,
    get_page_or_404,
    get_pages_for_locale,
    update_page,
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
SESSION_USER_KEY = "oxytail_user_id"


class AdminLoginRequired(Exception):
    def __init__(self, next_url: str) -> None:
        self.next_url = next_url


@dataclass(frozen=True)
class AdminMessage:
    kind: str
    text: str


def _login_url(next_path: str) -> str:
    return f"/admin/login/?next={quote(next_path, safe='/')}"


async def get_optional_user(request: Request) -> User | None:
    user_id = request.session.get(SESSION_USER_KEY)
    if not user_id:
        return None
    return await User.objects.get_or_none(id=user_id, is_active=True, is_staff=True)


async def require_user(request: Request) -> User:
    user = await get_optional_user(request)
    if user is None:
        raise AdminLoginRequired(str(request.url.path))
    return user


def _registered_field_names() -> set[str]:
    return {field.name for field in get_page_form_fields()}


def _form_values(page: Page | None = None, **overrides) -> dict:
    values = {
        "title": page.title if page else "",
        "slug": page.slug if page else "",
        "seo_title": page.seo_title or "" if page else "",
        "search_description": page.search_description or "" if page else "",
        "live": page.live if page else False,
        "show_in_menus": page.show_in_menus if page else False,
    }
    for field in get_page_form_fields():
        attr_value = getattr(page, field.name, None) if page is not None else None
        values[field.name] = attr_value or ""
    values.update(overrides)
    return values


def _body_value_for_save(*, page: Page | None, submitted_body: str) -> str | None:
    if "body" not in _registered_field_names():
        return page.body if page is not None else None
    return submitted_body or None


def _page_form_kwargs() -> dict:
    return {
        "extra_fields": get_page_form_fields(),
        "include_richtext_script": uses_richtext(),
    }


def create_admin_router() -> APIRouter:
    router = APIRouter(include_in_schema=False)

    @router.get("/login/")
    async def login_get(request: Request, next: str = "/admin/"):
        if await get_optional_user(request) is not None:
            return RedirectResponse(next, status_code=status.HTTP_303_SEE_OTHER)
        return html_response(LoginPage, next_url=next)

    @router.post("/login/")
    async def login_post(
        request: Request,
        username: Annotated[str, Form()],
        password: Annotated[str, Form()],
        next: Annotated[str, Form()] = "/admin/",
    ):
        user = await authenticate_user(username, password)
        if user is None:
            return html_response(LoginPage, error="Invalid username or password.", next_url=next)
        request.session[SESSION_USER_KEY] = user.id
        return RedirectResponse(next or "/admin/", status_code=status.HTTP_303_SEE_OTHER)

    @router.post("/logout/")
    async def logout_post(request: Request):
        request.session.clear()
        return RedirectResponse("/admin/login/", status_code=status.HTTP_303_SEE_OTHER)

    @router.get("/")
    async def dashboard(user: Annotated[User, Depends(require_user)]):
        locale = await get_admin_locale()
        page_count = len(await Page.objects.filter(locale_id=locale.id).all())
        return html_response(
            DashboardPage,
            username=user.username,
            page_count=page_count,
            locale_name=locale.display_name,
        )

    @router.get("/locales/")
    async def locales_list(user: Annotated[User, Depends(require_user)]):
        locales = await get_all_locales()
        return html_response(LocaleListPage, username=user.username, locales=locales)

    @router.get("/locales/add/")
    async def locales_add_get(user: Annotated[User, Depends(require_user)]):
        return html_response(LocaleAddPage, username=user.username, values=_form_values())

    @router.post("/locales/add/")
    async def locales_add_post(
        user: Annotated[User, Depends(require_user)],
        language_code: Annotated[str, Form()],
        display_name: Annotated[str, Form()],
        is_default: Annotated[str | None, Form()] = None,
    ):
        values = {
            "language_code": language_code,
            "display_name": display_name,
            "is_default": is_default == "1",
        }
        code = language_code.strip().lower()
        if not code or not display_name.strip():
            return html_response(
                LocaleAddPage,
                username=user.username,
                values=values,
                error="Language code and display name are required.",
            )
        existing = await get_all_locales()
        if any(locale.language_code == code for locale in existing):
            return html_response(
                LocaleAddPage,
                username=user.username,
                values=values,
                error=f"Locale '{code}' already exists.",
            )
        locale = await create_locale(
            language_code=code,
            display_name=display_name.strip(),
            is_default=is_default == "1" or not existing,
        )
        await ensure_root_page(locale)
        return RedirectResponse("/admin/locales/", status_code=status.HTTP_303_SEE_OTHER)

    @router.get("/menus/")
    async def menus_list(user: Annotated[User, Depends(require_user)]):
        locale = await get_admin_locale()
        menus = await get_menus_for_locale(locale)
        return html_response(
            MenuListPage,
            username=user.username,
            menus=menus,
            locale_name=locale.display_name,
        )

    @router.get("/menus/add/")
    async def menus_add_get(user: Annotated[User, Depends(require_user)]):
        return html_response(
            MenuAddPage,
            username=user.username,
            values={"is_active": True},
        )

    @router.post("/menus/add/")
    async def menus_add_post(
        user: Annotated[User, Depends(require_user)],
        name: Annotated[str, Form()],
        slug: Annotated[str, Form()],
        is_active: Annotated[str | None, Form()] = None,
    ):
        locale = await get_admin_locale()
        values = {"name": name, "slug": slug, "is_active": is_active == "1"}
        if not name.strip() or not slug.strip():
            return html_response(
                MenuAddPage,
                username=user.username,
                values=values,
                error="Name and slug are required.",
            )
        menu = await create_menu(
            name=name.strip(),
            slug=slug.strip().lower(),
            locale=locale,
            is_active=is_active == "1",
        )
        return RedirectResponse(f"/admin/menus/{menu.id}/", status_code=status.HTTP_303_SEE_OTHER)

    @router.get("/menus/{menu_id}/")
    async def menus_detail(menu_id: int, user: Annotated[User, Depends(require_user)]):
        locale = await get_admin_locale()
        menu = await get_menu_or_404(menu_id)
        items = await get_menu_items(menu)
        pages = await get_pages_for_locale(locale)
        return html_response(
            MenuDetailPage,
            username=user.username,
            menu=menu,
            items=items,
            pages=pages,
        )

    @router.post("/menus/{menu_id}/items/add/")
    async def menus_item_add(
        menu_id: int,
        user: Annotated[User, Depends(require_user)],
        label: Annotated[str, Form()],
        page_id: Annotated[str, Form()] = "",
        url: Annotated[str, Form()] = "",
        sort_order: Annotated[str, Form()] = "0",
        open_in_new_tab: Annotated[str | None, Form()] = None,
    ):
        menu = await get_menu_or_404(menu_id)
        locale = await get_admin_locale()
        values = {
            "label": label,
            "page_id": page_id,
            "url": url,
            "sort_order": sort_order,
            "open_in_new_tab": open_in_new_tab == "1",
        }
        if not label.strip():
            return html_response(
                MenuDetailPage,
                username=user.username,
                menu=menu,
                items=await get_menu_items(menu),
                pages=await get_pages_for_locale(locale),
                values=values,
                error="Label is required.",
            )
        page = None
        if page_id.strip():
            page = await get_page_or_404(int(page_id))
        elif not url.strip():
            return html_response(
                MenuDetailPage,
                username=user.username,
                menu=menu,
                items=await get_menu_items(menu),
                pages=await get_pages_for_locale(locale),
                values=values,
                error="Choose a page or provide an external URL.",
            )
        await create_menu_item(
            menu=menu,
            label=label.strip(),
            page=page,
            url=url.strip() or None,
            sort_order=int(sort_order or 0),
            open_in_new_tab=open_in_new_tab == "1",
        )
        return RedirectResponse(f"/admin/menus/{menu_id}/", status_code=status.HTTP_303_SEE_OTHER)

    @router.post("/menus/items/{item_id}/delete/")
    async def menus_item_delete(item_id: int, user: Annotated[User, Depends(require_user)]):
        item = await get_menu_item_or_404(item_id)
        menu_id = item.menu_id
        await item.delete()
        return RedirectResponse(f"/admin/menus/{menu_id}/", status_code=status.HTTP_303_SEE_OTHER)

    @router.get("/pages/")
    async def pages_root(user: Annotated[User, Depends(require_user)]):
        locale = await get_admin_locale()
        root = await ensure_root_page(locale)
        return RedirectResponse(f"/admin/pages/{root.id}/", status_code=status.HTTP_303_SEE_OTHER)

    @router.get("/pages/add/")
    async def page_add_get(
        user: Annotated[User, Depends(require_user)],
        parent: int | None = None,
    ):
        default_locale = await get_admin_locale()
        parent_page = (
            await get_page_or_404(parent)
            if parent
            else await ensure_root_page(default_locale)
        )
        breadcrumbs = await build_breadcrumbs(parent_page)
        breadcrumbs.append(type(breadcrumbs[-1])("Add child page", None))
        return html_response(
            PageFormPage,
            username=user.username,
            parent_page=parent_page,
            breadcrumbs=breadcrumbs,
            action_url=f"/admin/pages/add/?parent={parent_page.id}",
            title="Add child page",
            submit_label="Create page",
            values=_form_values(),
            **_page_form_kwargs(),
        )

    @router.post("/pages/add/")
    async def page_add_post(
        user: Annotated[User, Depends(require_user)],
        title: Annotated[str, Form()],
        slug: Annotated[str, Form()] = "",
        body: Annotated[str, Form()] = "",
        seo_title: Annotated[str, Form()] = "",
        search_description: Annotated[str, Form()] = "",
        live: Annotated[str | None, Form()] = None,
        show_in_menus: Annotated[str | None, Form()] = None,
        parent: int | None = None,
    ):
        default_locale = await get_admin_locale()
        parent_page = (
            await get_page_or_404(parent)
            if parent
            else await ensure_root_page(default_locale)
        )
        locale = await get_page_locale(parent_page)
        breadcrumbs = await build_breadcrumbs(parent_page)
        breadcrumbs.append(type(breadcrumbs[-1])("Add child page", None))
        values = _form_values(
            None,
            title=title,
            slug=slug,
            body=body,
            seo_title=seo_title,
            search_description=search_description,
            live=live == "1",
            show_in_menus=show_in_menus == "1",
        )
        if not title.strip():
            return html_response(
                PageFormPage,
                username=user.username,
                parent_page=parent_page,
                breadcrumbs=breadcrumbs,
                action_url=f"/admin/pages/add/?parent={parent_page.id}",
                title="Add child page",
                submit_label="Create page",
                values=values,
                error="Title is required.",
                **_page_form_kwargs(),
            )
        page = await create_child_page(
            parent=parent_page,
            title=title.strip(),
            slug=slug,
            locale=locale,
            body=_body_value_for_save(page=None, submitted_body=body),
            live=live == "1",
            show_in_menus=show_in_menus == "1",
            seo_title=seo_title or None,
            search_description=search_description or None,
        )
        return RedirectResponse(f"/admin/pages/{page.id}/edit/", status_code=status.HTTP_303_SEE_OTHER)

    @router.get("/pages/{page_id}/")
    async def page_listing(page_id: int, user: Annotated[User, Depends(require_user)]):
        page = await get_page_or_404(page_id)
        children = await get_child_pages(page)
        locale_sections = await build_all_locale_trees()
        breadcrumbs = await build_breadcrumbs(page)
        return html_response(
            PageListingPage,
            username=user.username,
            parent_page=page,
            children=children,
            locale_sections=locale_sections,
            breadcrumbs=breadcrumbs,
        )

    @router.get("/pages/{page_id}/edit/")
    async def page_edit_get(page_id: int, user: Annotated[User, Depends(require_user)]):
        page = await get_page_or_404(page_id)
        breadcrumbs = await build_breadcrumbs(page)
        breadcrumbs.append(type(breadcrumbs[-1])("Edit", None))
        return html_response(
            PageFormPage,
            username=user.username,
            page=page,
            breadcrumbs=breadcrumbs,
            action_url=f"/admin/pages/{page_id}/edit/",
            title=f"Editing {page.title}",
            submit_label="Save draft",
            values=_form_values(page),
            **_page_form_kwargs(),
        )

    @router.post("/pages/{page_id}/edit/")
    async def page_edit_post(
        page_id: int,
        user: Annotated[User, Depends(require_user)],
        title: Annotated[str, Form()],
        slug: Annotated[str, Form()] = "",
        body: Annotated[str, Form()] = "",
        seo_title: Annotated[str, Form()] = "",
        search_description: Annotated[str, Form()] = "",
        live: Annotated[str | None, Form()] = None,
        show_in_menus: Annotated[str | None, Form()] = None,
    ):
        page = await get_page_or_404(page_id)
        breadcrumbs = await build_breadcrumbs(page)
        breadcrumbs.append(type(breadcrumbs[-1])("Edit", None))
        values = _form_values(
            page,
            title=title,
            slug=slug,
            body=body,
            seo_title=seo_title,
            search_description=search_description,
            live=live == "1",
            show_in_menus=show_in_menus == "1",
        )
        if not title.strip():
            return html_response(
                PageFormPage,
                username=user.username,
                page=page,
                breadcrumbs=breadcrumbs,
                action_url=f"/admin/pages/{page_id}/edit/",
                title=f"Editing {page.title}",
                submit_label="Save draft",
                values=values,
                error="Title is required.",
                **_page_form_kwargs(),
            )
        await update_page(
            page,
            title=title.strip(),
            slug=slug,
            body=_body_value_for_save(page=page, submitted_body=body),
            live=live == "1",
            show_in_menus=show_in_menus == "1",
            seo_title=seo_title or None,
            search_description=search_description or None,
        )
        return RedirectResponse(f"/admin/pages/{page_id}/", status_code=status.HTTP_303_SEE_OTHER)

    @router.get("/pages/{page_id}/delete/")
    async def page_delete_get(page_id: int, user: Annotated[User, Depends(require_user)]):
        page = await get_page_or_404(page_id)
        breadcrumbs = await build_breadcrumbs(page)
        breadcrumbs.append(type(breadcrumbs[-1])("Delete", None))
        return html_response(
            DeletePagePage,
            username=user.username,
            page=page,
            breadcrumbs=breadcrumbs,
        )

    @router.post("/pages/{page_id}/delete/")
    async def page_delete_post(page_id: int, user: Annotated[User, Depends(require_user)]):
        page = await get_page_or_404(page_id)
        parent_id = page.parent_id
        await delete_page(page)
        if parent_id:
            return RedirectResponse(f"/admin/pages/{parent_id}/", status_code=status.HTTP_303_SEE_OTHER)
        locale = await get_admin_locale()
        root = await ensure_root_page(locale)
        return RedirectResponse(f"/admin/pages/{root.id}/", status_code=status.HTTP_303_SEE_OTHER)

    return router
