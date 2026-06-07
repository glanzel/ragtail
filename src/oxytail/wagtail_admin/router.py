from __future__ import annotations

import pyjsx.auto_setup  # noqa: F401
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from ..auth import authenticate_user
from ..models import Page, User
from .components.dashboard import DashboardPage
from .components.login import LoginPage
from .components.pages import DeletePagePage, PageFormPage, PageListingPage
from .render import html_response
from .services import (
    build_breadcrumbs,
    build_page_tree,
    create_child_page,
    delete_page,
    ensure_root_page,
    get_admin_locale,
    get_child_pages,
    get_page_or_404,
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


def _form_values(page: Page | None = None, **overrides) -> dict:
    values = {
        "title": page.title if page else "",
        "slug": page.slug if page else "",
        "body": page.body or "" if page else "",
        "seo_title": page.seo_title or "" if page else "",
        "search_description": page.search_description or "" if page else "",
        "live": page.live if page else False,
        "show_in_menus": page.show_in_menus if page else False,
    }
    values.update(overrides)
    return values


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

    @router.get("/pages/")
    async def pages_root(user: Annotated[User, Depends(require_user)]):
        locale = await get_admin_locale()
        root = await ensure_root_page(locale)
        return RedirectResponse(f"/admin/pages/{root.id}/", status_code=status.HTTP_303_SEE_OTHER)

    @router.get("/pages/{page_id}/")
    async def page_listing(page_id: int, user: Annotated[User, Depends(require_user)]):
        locale = await get_admin_locale()
        page = await get_page_or_404(page_id)
        children = await get_child_pages(page)
        tree = await build_page_tree(locale)
        breadcrumbs = await build_breadcrumbs(page)
        return html_response(
            PageListingPage,
            username=user.username,
            parent_page=page,
            children=children,
            tree=tree,
            breadcrumbs=breadcrumbs,
        )

    @router.get("/pages/add/")
    async def page_add_get(
        user: Annotated[User, Depends(require_user)],
        parent: int | None = None,
    ):
        locale = await get_admin_locale()
        parent_page = await get_page_or_404(parent) if parent else await ensure_root_page(locale)
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
        locale = await get_admin_locale()
        parent_page = await get_page_or_404(parent) if parent else await ensure_root_page(locale)
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
            )
        page = await create_child_page(
            parent=parent_page,
            title=title.strip(),
            slug=slug,
            locale=locale,
            body=body or None,
            live=live == "1",
            show_in_menus=show_in_menus == "1",
            seo_title=seo_title or None,
            search_description=search_description or None,
        )
        return RedirectResponse(f"/admin/pages/{page.id}/edit/", status_code=status.HTTP_303_SEE_OTHER)

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
            )
        await update_page(
            page,
            title=title.strip(),
            slug=slug,
            body=body or None,
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

