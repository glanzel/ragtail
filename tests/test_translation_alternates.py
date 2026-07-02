from pathlib import Path

import pytest
from oxyde import db

from ragtail.db import run_migrations
from ragtail.models import Locale
from ragtail.pages import create_page, create_translation
from ragtail.routing import get_translation_alternates
from ragtail.ragtail_admin.services import ensure_root_page
from ragtail.sites import ensure_default_site, ensure_tree_root, set_site_root_page


@pytest.mark.asyncio
async def test_translation_alternates_link_to_localized_paths(tmp_path: Path) -> None:
    database_url = f"sqlite:////{tmp_path / 'alternates.db'}"
    await db.init(default=database_url)
    try:
        connection = await db.get_connection("default")
        await run_migrations(connection)

        en = await Locale.objects.create(
            language_code="en",
            display_name="English",
            is_default=True,
            is_active=True,
        )
        de = await Locale.objects.create(
            language_code="de",
            display_name="Deutsch",
            is_default=False,
            is_active=True,
        )

        home = await ensure_root_page(en)
        site = await ensure_default_site()
        await set_site_root_page(site, home)
        de_tree_root = await ensure_tree_root(de)
        de_home = await create_translation(
            home,
            title="Zuhause",
            slug="",
            locale=de,
            parent=de_tree_root,
            live=True,
        )

        about = await create_page(
            title="About",
            slug="about",
            parent=home,
            locale=en,
            live=True,
        )
        await create_translation(
            about,
            title="Ueber uns",
            slug="ueber",
            locale=de,
            parent=de_home,
            live=True,
        )

        alternates = await get_translation_alternates(about, current_locale=en)
        by_code = {item.language_code: item for item in alternates}

        assert set(by_code) == {"en", "de"}
        assert by_code["en"].url == "/about/"
        assert by_code["en"].is_current is True
        assert by_code["de"].url == "/de/ueber/"
        assert by_code["de"].is_current is False
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_translation_alternates_skip_missing_translations(tmp_path: Path) -> None:
    database_url = f"sqlite:////{tmp_path / 'alternates-missing.db'}"
    await db.init(default=database_url)
    try:
        connection = await db.get_connection("default")
        await run_migrations(connection)

        en = await Locale.objects.create(
            language_code="en",
            display_name="English",
            is_default=True,
            is_active=True,
        )
        de = await Locale.objects.create(
            language_code="de",
            display_name="Deutsch",
            is_default=False,
            is_active=True,
        )
        fr = await Locale.objects.create(
            language_code="fr",
            display_name="Francais",
            is_default=False,
            is_active=True,
        )

        home = await ensure_root_page(en)
        site = await ensure_default_site()
        await set_site_root_page(site, home)
        de_tree_root = await ensure_tree_root(de)
        de_home = await create_translation(
            home,
            title="Zuhause",
            slug="",
            locale=de,
            parent=de_tree_root,
            live=True,
        )
        await ensure_tree_root(fr)

        about = await create_page(
            title="About",
            slug="about",
            parent=home,
            locale=en,
            live=True,
        )
        await create_translation(
            about,
            title="Ueber uns",
            slug="ueber",
            locale=de,
            parent=de_home,
            live=True,
        )

        alternates = await get_translation_alternates(about, current_locale=en)
        assert {item.language_code for item in alternates} == {"en", "de"}
    finally:
        await db.close()
