from __future__ import annotations

from typing import Any, ClassVar

from fastapi import Request

from ..models import Page
from ..routing import RouteMatch


class PageView:
    """Wagtail-style view for a CMS page content type."""

    content_type: ClassVar[str] = "page"

    async def get_context(
        self,
        request: Request,
        page: Page,
        route: RouteMatch,
    ) -> dict[str, Any]:
        return {}

    def get_template_name(self, request: Request, page: Page, route: RouteMatch) -> str:
        return f"{self.content_type}.html"
