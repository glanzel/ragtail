from __future__ import annotations

from oxyde import db

from ragtail.auth import ensure_superuser
from ragtail.db import ensure_tables
from ragtail.menus import create_menu, create_menu_item
from ragtail.models import Locale, Page, User
from ragtail.page_types import cast_page, get_content_type, get_default_page_model, persist_page
from ragtail.pages import create_page
from ragtail.ragtail_admin.services import ensure_root_page

from pages import ContentPage


async def _normalize_legacy_page_content_types() -> None:
    """Upgrade rows still using the generic ``page`` content type."""
    default_model = get_default_page_model()
    if default_model is Page:
        return

    target_content_type = get_content_type(default_model)
    legacy_pages = await Page.objects.filter(content_type="page").all()
    for row in legacy_pages:
        typed = await cast_page(row)
        typed.content_type = target_content_type
        await persist_page(typed)


async def seed_if_empty(
    *,
    admin_username: str = "admin",
    admin_password: str = "admin",
) -> None:
    database = await db.get_connection("default")
    await ensure_tables(database)
    await _normalize_legacy_page_content_types()

    if await User.objects.first() is not None:
        return

    await ensure_superuser(username=admin_username, password=admin_password)

    en = await Locale.objects.create(
        language_code="en",
        display_name="English",
        is_default=True,
        is_active=True,
    )

    home = await ensure_root_page(en)
    home.title = "Home"
    home.body = (
        "# Welcome to Oxytail\n\n"
        "This is the **demo site**. Page bodies are stored as Markdown and rendered to HTML "
        "on the public site.\n\n"
        "Edit content in the Wagtail-style admin at `/admin/`."
    )
    home.live = True
    home.show_in_menus = True
    await persist_page(home)

    about = await create_page(
        title="About",
        slug="about",
        parent=home,
        locale=en,
        live=True,
        show_in_menus=True,
        page_model=ContentPage,
        body=(
            "## About this demo\n\n"
            "Content is stored as **Markdown** in the database and converted to HTML when "
            "the page is served."
        ),
    )

    await create_page(
        title="Blog",
        slug="blog",
        parent=home,
        locale=en,
        live=True,
        show_in_menus=True,
        page_model=ContentPage,
        body="## Blog\n\nExample section with a classic Markdown body field.",
        content=[
            {
                "id": "demo0001",
                "type": "markdown_text",
                "value": "## StreamField demo\n\nThis section uses the new **StreamField** with Markdown, HTML, and image blocks.",
            },
            {
                "id": "demo0002",
                "type": "html_text",
                "value": "<p><em>HTML blocks</em> are stored as sanitized HTML and rendered directly.</p>",
            },
        ],
    )

    main_menu = await create_menu(name="Main", slug="main", locale=en)
    await create_menu_item(menu=main_menu, label="Home", page=home)
    await create_menu_item(menu=main_menu, label="About", page=about)
