from __future__ import annotations

import importlib
from collections.abc import Callable
from typing import Any

from fastapi import Request

from ..models import Page
from ..page_types import (
    content_type_to_component_name,
    get_content_type,
    get_default_page_model,
    get_page_model,
)
from ..routing import RouteMatch
from .base import BaseTemplateEngine, resolve_page_and_context

PyJsxComponent = Callable[..., Any]

_components: dict[str, PyJsxComponent] = {}


def register_pyjsx_component(content_type: str, component: PyJsxComponent) -> PyJsxComponent:
    """Register a PyJSX component for a page content type."""
    if content_type in _components:
        msg = f"PyJSX component for content type '{content_type}' is already registered"
        raise ValueError(msg)
    _components[content_type] = component
    return component


def clear_pyjsx_components() -> None:
    """Reset registered PyJSX components (mainly for tests)."""
    _components.clear()


class PyJsxRenderer(BaseTemplateEngine):
    """Render public pages with PyJSX components."""

    def __init__(
        self,
        components: dict[str, PyJsxComponent] | None = None,
        *,
        components_module: str | None = None,
    ) -> None:
        self._components = dict(_components)
        if components:
            self._components.update(components)
        self._components_module = components_module

    def register(self, content_type: str, component: PyJsxComponent) -> PyJsxComponent:
        self._components[content_type] = component
        return component

    def _resolve_component_content_type(self, content_type: str) -> str:
        if get_page_model(content_type) is not Page:
            return content_type
        default_model = get_default_page_model()
        if default_model is not Page:
            return get_content_type(default_model)
        return content_type

    def _lookup_component(self, content_type: str) -> PyJsxComponent:
        resolved_content_type = self._resolve_component_content_type(content_type)
        if resolved_content_type in self._components:
            return self._components[resolved_content_type]

        component_name = content_type_to_component_name(resolved_content_type)
        if self._components_module:
            module = importlib.import_module(self._components_module)
            component = getattr(module, component_name, None)
            if component is not None:
                self._components[resolved_content_type] = component
                if resolved_content_type != content_type:
                    self._components[content_type] = component
                return component

        msg = (
            f"No PyJSX component found for content type '{content_type}' "
            f"(expected '{component_name}(page, context)')"
        )
        raise LookupError(msg)

    async def serve(self, request: Request, route: RouteMatch) -> str:
        page, context = await resolve_page_and_context(request, route)
        component = self._lookup_component(page.content_type or "page")
        result = component(page=page, context=context)
        return str(result)
