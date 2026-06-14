from __future__ import annotations

import importlib
from collections.abc import Callable
from typing import Any

from fastapi import Request

from ..routing import RouteMatch
from .base import BaseTemplateEngine, content_type_to_component_name, resolve_view_and_context

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

    def _lookup_component(self, content_type: str) -> PyJsxComponent:
        if content_type in self._components:
            return self._components[content_type]

        component_name = content_type_to_component_name(content_type)
        if self._components_module:
            module = importlib.import_module(self._components_module)
            component = getattr(module, component_name, None)
            if component is not None:
                self._components[content_type] = component
                return component

        msg = (
            f"No PyJSX component found for content type '{content_type}' "
            f"(expected '{component_name}(page, context)')"
        )
        raise LookupError(msg)

    async def serve(self, request: Request, route: RouteMatch) -> str:
        _view, context = await resolve_view_and_context(request, route)
        component = self._lookup_component(route.page.content_type or "page")
        result = component(page=route.page, context=context)
        return str(result)
