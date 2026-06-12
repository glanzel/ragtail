from pathlib import Path

import pytest
from oxyde import db

from oxytail.db import run_migrations

from oxytail.models import Locale
from oxytail.pages import create_page, create_translation
from oxytail.routing import resolve_route
from oxytail.wagtail_admin.services import ensure_root_page


@pytest.mark.asyncio
async def test_resolve_route_falls_back_to_default_locale_page(tmp_path: Path) -> None:
    database_url = f"sqlite:////{tmp_path / 'fallback.db'}"
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
        about = await create_page(
            title="About",
            slug="about",
            parent=home,
            locale=en,
            live=True,
        )
        await ensure_root_page(de)
        await create_translation(
            about,
            title="Ueber uns",
            slug="ueber-uns",
            locale=de,
            parent=await ensure_root_page(de),
            live=True,
        )

        direct = await resolve_route("/de/ueber-uns/")
        assert direct is not None
        assert direct.page.title == "Ueber uns"
        assert direct.is_fallback is False

        fallback = await resolve_route("/de/about/")
        assert fallback is not None
        assert fallback.page.title == "About"
        assert fallback.locale.language_code == "de"
        assert fallback.is_fallback is True
    finally:
        await db.close()
