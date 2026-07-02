from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from oxyde import Field, Index, Model

if TYPE_CHECKING:
    from fastapi import Request

    from .routing import RouteMatch


class TimestampedModel(Model):
    """Shared timestamp fields for CMS tables."""

    created_at: datetime | None = Field(default=None, db_default="CURRENT_TIMESTAMP")
    updated_at: datetime | None = Field(default=None, db_default="CURRENT_TIMESTAMP")

    async def pre_save(
        self,
        *,
        is_create: bool,
        update_fields: set[str] | None = None,
    ) -> None:
        now = datetime.now(UTC).replace(tzinfo=None)
        if is_create and self.created_at is None:
            self.created_at = now
        self.updated_at = now


class Locale(TimestampedModel):
    """Language/locale configuration used by pages and menus."""

    id: int | None = Field(default=None, db_pk=True)
    language_code: str = Field(max_length=16, db_unique=True, db_index=True)
    display_name: str = Field(max_length=120)
    is_default: bool = Field(default=False, db_index=True)
    is_active: bool = Field(default=True, db_index=True)
    sort_order: int = Field(default=0, db_index=True)

    class Meta:
        is_table = True
        table_name = "oxytail_locales"


class Page(TimestampedModel):
    """Hierarchical, translatable CMS page inspired by Wagtail's core Page model."""

    id: int | None = Field(default=None, db_pk=True)
    title: str = Field(max_length=255, db_index=True)
    slug: str = Field(max_length=120, db_index=True)
    path: str = Field(max_length=512, db_index=True)
    depth: int = Field(default=1, db_index=True)
    sort_order: int = Field(default=0, db_index=True)

    locale: Locale | None = Field(default=None, db_on_delete="RESTRICT")
    translation_key: str | None = Field(default=None, max_length=36, db_index=True)
    parent: Page | None = Field(default=None, db_on_delete="CASCADE")
    children: list[Page] = Field(default=[], db_reverse_fk="parent")

    content_type: str = Field(default="page", max_length=100, db_index=True)
    page_data: str | None = Field(default=None, db_type="TEXT")
    body: str | None = Field(default=None, db_type="TEXT")
    seo_title: str | None = Field(default=None, max_length=255)
    search_description: str | None = Field(default=None, max_length=500)

    live: bool = Field(default=False, db_index=True)
    show_in_menus: bool = Field(default=False, db_index=True)
    first_published_at: datetime | None = Field(default=None)
    last_published_at: datetime | None = Field(default=None)

    class Meta:
        is_table = True
        table_name = "oxytail_pages"
        unique_together = [("locale", "path")]
        indexes = [
            Index(("locale", "slug")),
            Index(("parent", "sort_order")),
            Index(("translation_key", "locale")),
        ]

    async def pre_save(
        self,
        *,
        is_create: bool,
        update_fields: set[str] | None = None,
    ) -> None:
        from .seo import normalize_search_description

        self.search_description = normalize_search_description(self.search_description)
        await super().pre_save(is_create=is_create, update_fields=update_fields)

    @property
    def url(self) -> str:
        return self.path

    @property
    def is_tree_root(self) -> bool:
        return self.content_type == "tree_root"

    @property
    def is_root(self) -> bool:
        """True for the invisible technical tree root node."""
        return self.parent is None and self.is_tree_root

    async def get_context(self, request: Request, route: RouteMatch) -> dict[str, Any]:
        """Return extra template context (override in Page subclasses)."""
        from .routing import get_translation_alternates

        _ = request
        alternates = await get_translation_alternates(self, current_locale=route.locale)
        return {
            "translation_alternates": [alternate.as_dict() for alternate in alternates],
        }

    def get_template_name(self, request: Request, route: RouteMatch) -> str:
        """Default Wagtail-style template: ``about_page.html`` for ``AboutPage``."""
        _ = request, route
        from .page_types import class_to_content_type, get_page_model

        model_cls = get_page_model(self.content_type or "page")
        return f"{class_to_content_type(model_cls.__name__)}.html"


class Site(TimestampedModel):
    """Maps a hostname to the default-language homepage (Wagtail-style)."""

    id: int | None = Field(default=None, db_pk=True)
    hostname: str = Field(max_length=255, db_index=True)
    port: int = Field(default=80)
    site_name: str | None = Field(default=None, max_length=255)
    root_page: Page | None = Field(default=None, db_on_delete="SET NULL")
    is_default_site: bool = Field(default=False, db_index=True)
    prefix_default_language: bool = Field(default=False, db_index=True)

    class Meta:
        is_table = True
        table_name = "oxytail_sites"
        unique_together = [("hostname", "port")]


class Menu(TimestampedModel):
    """Named navigation menu for one locale."""

    id: int | None = Field(default=None, db_pk=True)
    name: str = Field(max_length=120)
    slug: str = Field(max_length=80, db_index=True)
    locale: Locale | None = Field(default=None, db_on_delete="CASCADE")
    is_active: bool = Field(default=True, db_index=True)

    class Meta:
        is_table = True
        table_name = "oxytail_menus"
        unique_together = [("locale", "slug")]


class User(TimestampedModel):
    """CMS staff user for admin login (single role for now)."""

    id: int | None = Field(default=None, db_pk=True)
    username: str = Field(max_length=150, db_unique=True, db_index=True)
    email: str = Field(max_length=254, db_unique=True, db_index=True)
    password_hash: str = Field(max_length=255)
    is_active: bool = Field(default=True, db_index=True)
    is_staff: bool = Field(default=True, db_index=True)

    class Meta:
        is_table = True
        table_name = "oxytail_users"


class MenuItem(TimestampedModel):
    """A menu entry that can point to an internal Page or an external URL."""

    id: int | None = Field(default=None, db_pk=True)
    menu: Menu | None = Field(default=None, db_on_delete="CASCADE")
    parent: MenuItem | None = Field(default=None, db_on_delete="CASCADE")
    children: list[MenuItem] = Field(default=[], db_reverse_fk="parent")

    label: str = Field(max_length=120)
    page: Page | None = Field(default=None, db_on_delete="SET NULL")
    url: str | None = Field(default=None, max_length=512)
    sort_order: int = Field(default=0, db_index=True)
    is_active: bool = Field(default=True, db_index=True)
    open_in_new_tab: bool = Field(default=False)

    class Meta:
        is_table = True
        table_name = "oxytail_menu_items"
        indexes = [
            Index(("menu", "parent", "sort_order")),
        ]

    @property
    def href(self) -> str:
        if self.page is not None:
            return self.page.url
        return self.url or "#"

    async def resolve_href(self) -> str:
        if self.page is not None:
            from .routing import get_page_public_url

            public_url = await get_page_public_url(self.page)
            if public_url is not None:
                return public_url
            return self.page.url
        return self.url or "#"
