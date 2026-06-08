from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from oxyde import create_tables, db

from oxytail.auth import ensure_superuser
from oxytail.fastapi import create_app
from oxytail.models import Locale
from oxytail.pages import create_page
from oxytail.wagtail_admin.services import ensure_root_page


@pytest_asyncio.fixture
async def client(tmp_path: Path):
    database_url = f"sqlite:///{tmp_path / 'admin.db'}"
    await db.init(default=database_url)
    try:
        connection = await db.get_connection("default")
        await create_tables(connection)
        await ensure_superuser(username="admin", password="admin")
        en = await Locale.objects.create(
            language_code="en",
            display_name="English",
            is_default=True,
            is_active=True,
        )
        home = await ensure_root_page(en)
        await create_page(
            title="About",
            slug="about",
            parent=home,
            locale=en,
            live=True,
        )

        app = create_app(
            database_url=database_url,
            mount_wagtail_admin=True,
            secret_key="test-secret",
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as http_client:
            yield http_client
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_admin_requires_login(client: AsyncClient) -> None:
    response = await client.get("/admin/pages/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"].startswith("/admin/login/")


@pytest.mark.asyncio
async def test_admin_login_and_page_explorer(client: AsyncClient) -> None:
    login = await client.post(
        "/admin/login/",
        data={"username": "admin", "password": "admin", "next": "/admin/"},
        follow_redirects=False,
    )
    assert login.status_code == 303
    assert login.headers["location"] == "/admin/"

    dashboard = await client.get("/admin/", cookies=login.cookies)
    assert dashboard.status_code == 200
    assert "Welcome to the Wagtail CMS" in dashboard.text

    pages = await client.get("/admin/pages/", cookies=login.cookies, follow_redirects=False)
    assert pages.status_code == 303
    root_id = pages.headers["location"].rstrip("/").rsplit("/", 1)[-1]

    listing = await client.get(f"/admin/pages/{root_id}/", cookies=login.cookies)
    assert listing.status_code == 200
    assert "Add child page" in listing.text
    assert "About" in listing.text


@pytest.mark.asyncio
async def test_admin_page_add_route(client: AsyncClient) -> None:
    login = await client.post(
        "/admin/login/",
        data={"username": "admin", "password": "admin", "next": "/admin/pages/"},
        follow_redirects=False,
    )
    pages = await client.get("/admin/pages/", cookies=login.cookies, follow_redirects=False)
    root_id = pages.headers["location"].rstrip("/").rsplit("/", 1)[-1]

    add_page = await client.get(
        f"/admin/pages/add/?parent={root_id}",
        cookies=login.cookies,
    )
    assert add_page.status_code == 200
    assert "Add child page" in add_page.text


@pytest.mark.asyncio
async def test_admin_page_explorer_shows_all_locales(client: AsyncClient) -> None:
    login = await client.post(
        "/admin/login/",
        data={"username": "admin", "password": "admin", "next": "/admin/pages/"},
        follow_redirects=False,
    )
    await client.post(
        "/admin/locales/add/",
        data={"language_code": "de", "display_name": "Deutsch"},
        cookies=login.cookies,
        follow_redirects=False,
    )

    pages = await client.get("/admin/pages/", cookies=login.cookies, follow_redirects=False)
    root_id = pages.headers["location"].rstrip("/").rsplit("/", 1)[-1]

    listing = await client.get(f"/admin/pages/{root_id}/", cookies=login.cookies)
    assert listing.status_code == 200
    assert "English" in listing.text
    assert "Deutsch" in listing.text
    assert "About" in listing.text
