from __future__ import annotations

from oxyde import db

from oxytail.auth import ensure_superuser
from oxytail.db import ensure_tables
from oxytail.menus import create_menu, create_menu_item
from oxytail.models import Locale, Page, User
from oxytail.pages import create_page
from oxytail.wagtail_admin.services import ensure_root_page


async def seed_if_empty(
    *,
    admin_username: str = "admin",
    admin_password: str = "admin",
) -> None:
    database = await db.get_connection("default")
    await ensure_tables(database)

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
    await home.save()

    about = await create_page(
        title="About",
        slug="about",
        parent=home,
        locale=en,
        live=True,
        show_in_menus=True,
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
        body="## Blog\n\nExample section. StreamField blocks can come later.",
    )

    main_menu = await create_menu(name="Main", slug="main", locale=en)
    await create_menu_item(menu=main_menu, label="Home", page=home)
    await create_menu_item(menu=main_menu, label="About", page=about)
