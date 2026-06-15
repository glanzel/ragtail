from pathlib import Path

import pytest
from oxyde import AsyncDatabase, create_tables

from ragtail.menus import create_menu, create_menu_item, get_menu_tree
from ragtail.models import Locale
from ragtail.pages import create_page, create_translation
from ragtail.routing import resolve_route


@pytest.mark.asyncio
async def test_pages_routes_and_menus_work_with_oxyde(tmp_path: Path) -> None:
    database = AsyncDatabase(f"sqlite:////{tmp_path / 'cms.db'}", name="default")

    async with database:
        await create_tables(database)

        en = await Locale.objects.create(
            language_code="en",
            display_name="English",
            is_default=True,
        )
        de = await Locale.objects.create(language_code="de", display_name="Deutsch")

        home = await create_page(title="Home", slug="", locale=en, live=True)
        about = await create_page(title="About", slug="about", parent=home, locale=en, live=True)
        await create_translation(
            about,
            title="Ueber uns",
            slug="ueber-uns",
            locale=de,
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
