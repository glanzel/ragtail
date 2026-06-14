from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from inspect import isawaitable
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response

from .admin import create_fastapi_admin
from .menus import get_menu_tree
from .models import Page
from .routing import RouteMatch, resolve_route

if TYPE_CHECKING:
    from .templates.base import TemplateEngineInterface

PageRenderer = Callable[[Request, RouteMatch], Response | Awaitable[Response]]
StartupHook = Callable[[], Awaitable[None]]


def default_page_payload(route: RouteMatch) -> dict[str, Any]:
    page = route.page
    return {
        "id": page.id,
        "title": page.title,
        "slug": page.slug,
        "path": route.public_path,
        "locale": route.locale.language_code,
        "content_type": page.content_type,
        "body": page.body,
        "seo_title": page.seo_title,
        "search_description": page.search_description,
        "is_fallback": route.is_fallback,
    }


async def default_page_renderer(_request: Request, route: RouteMatch) -> Response:
    return JSONResponse(default_page_payload(route))


def create_cms_router(
    *,
    renderer: PageRenderer | None = None,
    include_unpublished: bool = False,
    prefix_default_language: bool = False,
) -> APIRouter:
    """Create a catch-all router that resolves Page objects from request paths."""

    router = APIRouter()
    page_renderer = renderer or default_page_renderer

    @router.get("/{full_path:path}", include_in_schema=False)
    async def serve_page(request: Request, full_path: str = "") -> Response:
        route = await resolve_route(
            f"/{full_path}",
            include_unpublished=include_unpublished,
            prefix_default_language=prefix_default_language,
        )
        if route is None:
            raise HTTPException(status_code=404, detail="Page not found")

        result = page_renderer(request, route)
        if isawaitable(result):
            return await result
        return result

    return router


def create_api_router() -> APIRouter:
    """Small JSON API for pages and menus that can sit beside the CMS catch-all."""

    router = APIRouter(prefix="/api/cms", tags=["cms"])

    @router.get("/pages/{path:path}")
    async def page_detail(path: str, language: str | None = None) -> dict[str, Any]:
        route = await resolve_route(path, language_code=language)
        if route is None:
            raise HTTPException(status_code=404, detail="Page not found")
        return default_page_payload(route)

    @router.get("/menus/{slug}")
    async def menu_detail(slug: str, language: str | None = None) -> dict[str, Any]:
        tree = await get_menu_tree(slug, language_code=language)
        return {"slug": slug, "items": [node.as_dict() for node in tree]}

    return router


def create_app(
    *,
    database_url: str = "sqlite://oxytail.db",
    renderer: PageRenderer | None = None,
    template_engine: TemplateEngineInterface | None = None,
    mount_admin: bool = False,
    mount_wagtail_admin: bool = False,
    admin_path: str = "/admin",
    secret_key: str = "change-me-in-production",
    title: str = "Oxytail CMS",
    startup_hook: StartupHook | None = None,
) -> FastAPI:
    """Create a runnable FastAPI app using Oxyde's lifespan integration."""
    from .cms import FastAPICMS

    cms = FastAPICMS(
        secret_key=secret_key,
        title=title,
        prefix=admin_path,
        renderer=renderer,
        template_engine=template_engine,
    )
    app = FastAPI(
        title=title,
        lifespan=cms.lifespan(database_url, startup_hook=startup_hook),
    )
    app.include_router(create_api_router())

    if mount_wagtail_admin:
        app.mount(admin_path.rstrip("/"), cms.app)

    if mount_admin:
        admin = create_fastapi_admin(title=f"{title} Admin", include_users=True)
        app.mount(admin_path, admin.app)

    app.include_router(create_cms_router(renderer=cms.renderer))
    return app


__all__ = [
    "Page",
    "PageRenderer",
    "RouteMatch",
    "create_api_router",
    "create_app",
    "create_cms_router",
    "default_page_payload",
]
