from __future__ import annotations

from typing import Any

from .models import Locale, Menu, MenuItem, Page, Site, User


def register_cms_models(admin: Any, *, include_users: bool = False) -> Any:
    """Register Oxytail models on an oxyde-admin compatible admin instance."""

    admin.register(
        Locale,
        list_display=["language_code", "display_name", "is_default", "is_active", "sort_order"],
        search_fields=["language_code", "display_name"],
        list_filter=["is_default", "is_active"],
    )
    admin.register(
        Site,
        list_display=["hostname", "port", "site_name", "locale", "root_page", "is_default_site"],
        list_filter=["is_default_site"],
    )
    admin.register(
        Page,
        list_display=["title", "slug", "path", "locale", "live", "show_in_menus", "sort_order"],
        search_fields=["title", "slug", "path", "body"],
        list_filter=["locale", "live", "show_in_menus", "content_type"],
    )
    admin.register(
        Menu,
        list_display=["name", "slug", "locale", "is_active"],
        search_fields=["name", "slug"],
        list_filter=["locale", "is_active"],
    )
    admin.register(
        MenuItem,
        list_display=["label", "menu", "parent", "page", "url", "sort_order", "is_active"],
        search_fields=["label", "url"],
        list_filter=["menu", "is_active", "open_in_new_tab"],
    )
    if include_users:
        admin.register(
            User,
            list_display=["username", "email", "is_active", "is_staff"],
            search_fields=["username", "email"],
            list_filter=["is_active", "is_staff"],
            readonly_fields=["password_hash"],
        )
    return admin


def create_fastapi_admin(
    *,
    title: str = "Oxytail Admin",
    include_users: bool = False,
) -> Any:
    """Create and register a FastAPI oxyde-admin instance."""

    try:
        from oxyde_admin import FastAPIAdmin
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        raise RuntimeError(
            "Install the admin extra to use the bundled admin: uv sync --extra admin"
        ) from exc

    admin = FastAPIAdmin(title=title)
    return register_cms_models(admin, include_users=include_users)
