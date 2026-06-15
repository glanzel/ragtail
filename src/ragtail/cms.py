from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from oxyde import db
from starlette.middleware.sessions import SessionMiddleware

from .db import prepare_sqlite_database, run_migrations
from .ragtail_admin.router import AdminLoginRequired, STATIC_DIR, _login_url, create_admin_router

if TYPE_CHECKING:
    from .fastapi import PageRenderer
    from .templates.base import TemplateEngineInterface

StartupHook = Callable[[], Awaitable[None]]


class FastAPICMS:
    """FastAPI adapter for Ragtail — mount like oxyde-admin's ``FastAPIAdmin``."""

    def __init__(
        self,
        *,
        secret_key: str = "change-me-in-production",
        title: str = "Ragtail",
        prefix: str = "/admin",
        renderer: PageRenderer | None = None,
        template_engine: TemplateEngineInterface | None = None,
        include_unpublished: bool = False,
        prefix_default_language: bool = False,
    ) -> None:
        self.secret_key = secret_key
        self.title = title
        self.prefix = prefix.rstrip("/") or "/admin"
        if renderer is not None:
            self.renderer = renderer
        elif template_engine is not None:
            self.renderer = template_engine.as_renderer()
        else:
            self.renderer = None
        self.template_engine = template_engine
        self.include_unpublished = include_unpublished
        self.prefix_default_language = prefix_default_language
        self._app: FastAPI | None = None

    @property
    def app(self) -> FastAPI:
        """Ragtail admin sub-application (mount at ``prefix``)."""
        if self._app is None:
            self._app = self._build_admin_app()
        return self._app

    @property
    def pages_router(self) -> APIRouter:
        """Catch-all router for public CMS pages — include last on the host app."""
        from .fastapi import create_cms_router

        return create_cms_router(
            renderer=self.renderer,
            include_unpublished=self.include_unpublished,
            prefix_default_language=self.prefix_default_language,
        )

    def lifespan(
        self,
        database_url: str,
        *,
        startup_hook: StartupHook | None = None,
    ) -> Callable[[FastAPI], AsyncIterator[None]]:
        """Return a FastAPI lifespan that opens the DB and applies Ragtail migrations."""
        prepare_sqlite_database(database_url)
        base_lifespan = db.lifespan(default=database_url)

        @asynccontextmanager
        async def cms_lifespan(app: FastAPI) -> AsyncIterator[None]:
            async with base_lifespan(app):
                await run_migrations()
                if startup_hook is not None:
                    await startup_hook()
                yield

        return cms_lifespan

    def mount(self, app: FastAPI, *, pages: bool = True, api: bool = True) -> None:
        """Attach the CMS admin (and optionally API + public pages) to an existing app."""
        from .fastapi import create_api_router

        app.mount(self.prefix, self.app)
        if api:
            app.include_router(create_api_router())
        if pages:
            app.include_router(self.pages_router)

    def _build_admin_app(self) -> FastAPI:
        admin = FastAPI(
            title=f"{self.title} Admin",
            docs_url=None,
            redoc_url=None,
        )
        admin.add_middleware(SessionMiddleware, secret_key=self.secret_key)
        admin.mount("/static", StaticFiles(directory=STATIC_DIR), name="ragtail_admin_static")
        admin.include_router(create_admin_router())

        @admin.exception_handler(AdminLoginRequired)
        async def admin_login_redirect(
            _request: Request,
            exc: AdminLoginRequired,
        ) -> RedirectResponse:
            return RedirectResponse(_login_url(exc.next_url), status_code=303)

        return admin


__all__ = ["FastAPICMS"]
