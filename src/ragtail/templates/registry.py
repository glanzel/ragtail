from __future__ import annotations

from typing import TypeVar

from .views import PageView

T = TypeVar("T", bound=type[PageView])

_page_views: dict[str, type[PageView]] = {}
_default_page_view: type[PageView] = PageView


def register_page_view(view_cls: T) -> T:
    """Register a PageView class for its ``content_type``."""
    content_type = view_cls.content_type
    if content_type in _page_views:
        msg = f"Page view for content type '{content_type}' is already registered"
        raise ValueError(msg)
    _page_views[content_type] = view_cls
    return view_cls


def get_page_view(content_type: str) -> PageView:
    """Return a PageView instance for the given content type."""
    view_cls = _page_views.get(content_type, _default_page_view)
    return view_cls()


def clear_page_views() -> None:
    """Reset registered views (mainly for tests)."""
    _page_views.clear()
