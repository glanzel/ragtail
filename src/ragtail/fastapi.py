from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from inspect import isawaitable
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response

from .admin import create_fastapi_admin
from .images.fields import image_field_names, image_field_renditions, image_to_api_dict
from .images.models import Image
from .menus import get_menu_tree
from .models import Page
from .page_types import cast_page, get_page_model
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


async def page_payload_with_fields(route: RouteMatch) -> dict[str, Any]:
    payload = default_page_payload(route)
    page = await cast_page(route.page)
    model_cls = get_page_model(page.content_type or "page")
    if model_cls is Page:
        return payload

    extra: dict[str, Any] = {}
    for name in image_field_names(model_cls):
        image = getattr(page, name, None)
        specs = image_field_renditions(model_cls.model_fields[name])
        extra[name] = await image_to_api_dict(image, renditions=specs)

    for name in model_cls.model_fields:
        if name in payload or name in extra:
            continue
        if name.startswith("_") or name in {"children", "page_data"}:
            continue
        if name in Page.model_fields and name not in {"body", "seo_title", "search_description"}:
            continue
        value = getattr(page, name, None)
        if name not in image_field_names(model_cls):
            extra[name] = value

    if extra:
        payload["fields"] = extra
    return payload


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
        return await page_payload_with_fields(route)

    @router.get("/images/{image_id}")
    async def image_detail(image_id: int) -> dict[str, Any]:
        image = await Image.objects.get_or_none(id=image_id)
        if image is None:
            raise HTTPException(status_code=404, detail="Image not found")
        payload = await image_to_api_dict(image)
        assert payload is not None
        return payload

    @router.get("/images/{image_id}/renditions/{filter_spec:path}")
    async def image_rendition(image_id: int, filter_spec: str) -> dict[str, Any]:
        image = await Image.objects.get_or_none(id=image_id)
        if image is None:
            raise HTTPException(status_code=404, detail="Image not found")
        try:
            rendition = await image.get_rendition(filter_spec)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        from .images.fields import rendition_to_api_dict

        return rendition_to_api_dict(rendition)

    @router.get("/menus/{slug}")
    async def menu_detail(slug: str, language: str | None = None) -> dict[str, Any]:
        tree = await get_menu_tree(slug, language_code=language)
        return {"slug": slug, "items": [node.as_dict() for node in tree]}

    return router


def create_app(
    *,
    renderer: PageRenderer | None = None,
    template_engine: TemplateEngineInterface | None = None,
    mount_admin: bool = False,
    mount_ragtail_admin: bool = False,
    admin_path: str = "/admin",
    secret_key: str = "change-me-in-production",
    title: str = "Ragtail CMS",
    startup_hook: StartupHook | None = None,
    api: bool = True,
    pages: bool = True,
    media_root: str | None = None,
    media_url: str = "/media/",
    **databases: str,
) -> FastAPI:
    """Create a runnable FastAPI app using Oxyde's lifespan integration.

    Reads ``DATABASES`` from ``oxyde_config.py`` when no database aliases are passed.
    """
    from .cms import FastAPICMS

    cms = FastAPICMS(
        secret_key=secret_key,
        title=title,
        prefix=admin_path,
        renderer=renderer,
        template_engine=template_engine,
        media_root=media_root,
        media_url=media_url,
    )
    app = FastAPI(
        title=title,
        lifespan=cms.lifespan(startup_hook=startup_hook, **databases),
    )

    if mount_ragtail_admin:
        cms.mount(app, pages=pages, api=api)
    else:
        if api:
            app.include_router(create_api_router())
        if pages:
            app.include_router(cms.pages_router)

    if mount_admin:
        admin = create_fastapi_admin(title=f"{title} Admin", include_users=True)
        app.mount(admin_path, admin.app)

    return app


__all__ = [
    "Page",
    "PageRenderer",
    "RouteMatch",
    "create_api_router",
    "create_app",
    "create_cms_router",
    "default_page_payload",
    "page_payload_with_fields",
]
