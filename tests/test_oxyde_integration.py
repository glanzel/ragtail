from __future__ import annotations

import pytest
from oxyde import db

from ragtail.db import run_migrations
from ragtail.menus import create_menu, create_menu_item, get_menu_tree
from ragtail.models import Locale
from ragtail.pages import create_page, create_translation
from ragtail.routing import resolve_route
from ragtail.sites import ensure_default_site, ensure_tree_root, set_site_root_page


@pytest.mark.asyncio
async def test_pages_routes_and_menus_work_with_oxyde(tmp_path) -> None:
    from oxyde import AsyncDatabase, db

    database_url = f"sqlite:////{tmp_path / 'cms.db'}"
    database = AsyncDatabase(database_url, name="default")

    async with database:
        await db.init(default=database_url)
        connection = await db.get_connection("default")
        await run_migrations(connection)

        en = await Locale.objects.create(
            language_code="en",
            display_name="English",
            is_default=True,
        )
        de = await Locale.objects.create(language_code="de", display_name="Deutsch")

        tree_root = await ensure_tree_root(en)
        site = await ensure_default_site()
        home = await create_page(title="Home", slug="", parent=tree_root, locale=en, live=True)
        await set_site_root_page(site, home)
        de_tree_root = await ensure_tree_root(de)
        de_home = await create_translation(
            home,
            title="Home",
            slug="",
            locale=de,
            parent=de_tree_root,
            live=True,
        )
        about = await create_page(title="About", slug="about", parent=home, locale=en, live=True)
        await create_translation(
            about,
            title="Ueber uns",
            slug="ueber-uns",
            locale=de,
            parent=de_home,
            live=True,
        )

        menu = await create_menu(name="Main", slug="main", locale=en)
        await create_menu_item(menu=menu, label="About", page=about)

        route = await resolve_route("/about/")
        menu_tree = await get_menu_tree("main", language_code="en")

        assert route is not None
        assert route.page.title == "About"
        assert route.public_path == "/about/"
        assert [item.as_dict() for item in menu_tree] == [
            {
                "id": 1,
                "label": "About",
                "href": "/about/",
                "open_in_new_tab": False,
                "children": [],
            }
        ]
