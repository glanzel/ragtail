from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from oxyde import db

from ragtail.auth import ensure_superuser
from ragtail.db import run_migrations
from ragtail.fastapi import create_app
from ragtail.models import Locale, Menu, Page
from ragtail.pages import create_page
from ragtail.ragtail_admin.services import ensure_root_page


@pytest_asyncio.fixture
async def client(tmp_path: Path, oxyde_config):
    database_url = oxyde_config(f"sqlite:////{tmp_path / 'admin-extra.db'}")
    await db.init(default=database_url)
    try:
        connection = await db.get_connection("default")
        await run_migrations(connection)
        await ensure_superuser(username="admin", password="admin")
        en = await Locale.objects.create(
            language_code="en",
            display_name="English",
            is_default=True,
            is_active=True,
        )
        home = await ensure_root_page(en)
        await create_page(title="About", slug="about", parent=home, locale=en, live=True)

        app = create_app(
            mount_ragtail_admin=True,
            secret_key="test-secret",
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as http_client:
            yield http_client
    finally:
        await db.close()


async def _login(client: AsyncClient) -> None:
    response = await client.post(
        "/admin/login/",
        data={"username": "admin", "password": "admin", "next": "/admin/"},
        follow_redirects=False,
    )
    assert response.status_code == 303


@pytest.mark.asyncio
async def test_add_locale_creates_second_language(client: AsyncClient) -> None:
    await _login(client)
    response = await client.post(
        "/admin/locales/add/",
        data={
            "language_code": "de",
            "display_name": "Deutsch",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/locales/"

    locales = await Locale.objects.order_by("language_code").all()
    assert len(locales) == 2
    assert any(locale.language_code == "de" for locale in locales)


@pytest.mark.asyncio
async def test_edit_locale_changes_default(client: AsyncClient) -> None:
    await _login(client)
    de = await Locale.objects.get_or_none(language_code="de")
    if de is None:
        await client.post(
            "/admin/locales/add/",
            data={"language_code": "de", "display_name": "Deutsch"},
            cookies=client.cookies,
            follow_redirects=False,
        )
        de = await Locale.objects.get_or_none(language_code="de")
    assert de is not None

    edit = await client.get(f"/admin/locales/{de.id}/edit/", cookies=client.cookies)
    assert edit.status_code == 200
    assert "Default locale" in edit.text

    save = await client.post(
        f"/admin/locales/{de.id}/edit/",
        data={
            "display_name": "Deutsch",
            "is_default": "1",
            "is_active": "1",
        },
        cookies=client.cookies,
        follow_redirects=False,
    )
    assert save.status_code == 303

    de = await Locale.objects.get_or_none(id=de.id)
    en = await Locale.objects.get_or_none(language_code="en")
    assert de is not None and en is not None
    assert de.is_default is True
    assert en.is_default is False


@pytest.mark.asyncio
async def test_menu_admin_locale_switcher(client: AsyncClient) -> None:
    await _login(client)
    await client.post(
        "/admin/locales/add/",
        data={"language_code": "de", "display_name": "Deutsch"},
        cookies=client.cookies,
        follow_redirects=False,
    )
    switch = await client.post(
        "/admin/set-locale/",
        data={"language_code": "de", "next": "/admin/menus/"},
        cookies=client.cookies,
        follow_redirects=False,
    )
    assert switch.status_code == 303
    await client.post(
        "/admin/menus/add/",
        data={"name": "Hauptmenue", "slug": "main", "is_active": "1"},
        cookies=client.cookies,
        follow_redirects=False,
    )
    listing = await client.get("/admin/menus/", cookies=client.cookies)
    assert listing.status_code == 200
    assert "Hauptmenue" in listing.text


@pytest.mark.asyncio
async def test_create_menu_and_item(client: AsyncClient) -> None:
    await _login(client)
    create_menu_response = await client.post(
        "/admin/menus/add/",
        data={"name": "Footer", "slug": "footer", "is_active": "1"},
        follow_redirects=False,
    )
    assert create_menu_response.status_code == 303
    menu = await Menu.objects.get_or_none(slug="footer")
    assert menu is not None

    about_page = await Page.objects.filter(slug="about").first()
    assert about_page is not None

    add_item = await client.post(
        f"/admin/menus/{menu.id}/items/add/",
        data={
            "label": "About us",
            "page_id": str(about_page.id),
            "sort_order": "0",
        },
        follow_redirects=False,
    )
    assert add_item.status_code == 303

    listing = await client.get(f"/admin/menus/{menu.id}/")
    assert listing.status_code == 200
    assert "About us" in listing.text
