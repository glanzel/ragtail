from __future__ import annotations

from datetime import UTC, datetime

from oxyde import Field, Index, Model


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

    @property
    def url(self) -> str:
        return self.path

    @property
    def is_root(self) -> bool:
        return self.parent is None and self.path == "/"


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
