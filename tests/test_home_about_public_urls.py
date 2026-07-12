"""Regression tests for Wagtail-like public URLs: / for home, /about/ for children."""

from __future__ import annotations

from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from oxyde import db

from ragtail.auth import ensure_superuser
from ragtail.db import run_migrations
from ragtail.fastapi import create_app
from ragtail.models import Locale, Page, Site
from ragtail.ragtail_admin.services import ensure_root_page
from ragtail.routing import get_page_public_url, resolve_route
from ragtail.sites import ensure_default_site, ensure_tree_root, get_default_site, upgrade_all_locales


async def _login(client: AsyncClient) -> None:
    response = await client.post(
        "/admin/login/",
        data={"username": "admin", "password": "admin", "next": "/admin/"},
        follow_redirects=False,
    )
    assert response.status_code == 303


@pytest_asyncio.fixture
async def public_app_client(tmp_path: Path, oxyde_config):
    """Fresh CMS app with lifespan (migrations + upgrade_all_locales), no pre-seeded pages."""

    database_url = oxyde_config(f"sqlite:////{tmp_path / 'home-about-urls.db'}")
    await db.init(default=database_url)
    try:
        connection = await db.get_connection("default")
        await run_migrations(connection)
        await ensure_superuser(username="admin", password="admin")
        await Locale.objects.create(
            language_code="en",
            display_name="English",
            is_default=True,
            is_active=True,
        )
        await ensure_tree_root(await Locale.objects.first())
        await ensure_default_site()

        app = create_app(
            mount_ragtail_admin=True,
            secret_key="test-secret",
            default=database_url,
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_admin_created_home_about_are_public_at_root_paths(
    public_app_client: AsyncClient,
) -> None:
    """Reproduce the manual admin flow: Home (slug home) -> About -> site root -> public URLs."""

    client = public_app_client
    await _login(client)

    locale = await Locale.objects.first()
    assert locale is not None
    tree_root = await ensure_tree_root(locale)
    assert tree_root.id is not None

    create_home = await client.post(
        f"/admin/pages/add/?parent={tree_root.id}",
        data={
            "title": "Home",
            "slug": "home",
            "live": "1",
            "show_in_menus": "1",
        },
        cookies=client.cookies,
        follow_redirects=False,
    )
    assert create_home.status_code == 303

    home = await Page.objects.filter(slug="home", locale_id=locale.id).first()
    assert home is not None

    create_about = await client.post(
        f"/admin/pages/add/?parent={home.id}",
        data={
            "title": "About",
            "slug": "about",
            "live": "1",
            "show_in_menus": "1",
        },
        cookies=client.cookies,
        follow_redirects=False,
    )
    assert create_about.status_code == 303

    about = await Page.objects.filter(slug="about", locale_id=locale.id).first()
    assert about is not None

    site = await get_default_site()
    assert site is not None and site.id is not None

    save_site = await client.post(
        f"/admin/sites/{site.id}/edit/",
        data={
            "hostname": site.hostname,
            "port": str(site.port),
            "site_name": "",
            "root_page_id": str(home.id),
            "is_default_site": "1",
        },
        cookies=client.cookies,
        follow_redirects=False,
    )
    assert save_site.status_code == 303, save_site.text

    home = await Page.objects.get(id=home.id)
    about = await Page.objects.get(id=about.id)
    site = await Site.objects.get(id=site.id)

    assert site.root_page_id == home.id
    assert home.path == "/", f"homepage should be stored at /, got {home.path!r}"
    assert about.path == "/about/", f"about should be stored at /about/, got {about.path!r}"

    home_url = await get_page_public_url(home)
    about_url = await get_page_public_url(about)
    assert home_url == "/"
    assert about_url == "/about/"

    home_route = await resolve_route("/")
    about_route = await resolve_route("/about/")
    legacy_route = await resolve_route("/home/about/")

    assert home_route is not None and home_route.page.id == home.id
    assert about_route is not None and about_route.page.id == about.id
    assert about_route.public_path == "/about/"
    assert legacy_route is None, "legacy /home/about/ must not resolve when homepage slug is omitted"

    home_response = await client.get("/")
    about_response = await client.get("/about/")
    legacy_response = await client.get("/home/about/")

    assert home_response.status_code == 200
    assert "Home" in home_response.text
    assert about_response.status_code == 200
    assert "About" in about_response.text
    assert legacy_response.status_code == 404


@pytest.mark.asyncio
async def test_about_added_from_pages_explorer_after_seed_home(
    public_app_client: AsyncClient,
) -> None:
    """Like demo seed + admin: existing site-root home, add About from /admin/pages/."""

    client = public_app_client
    await _login(client)

    locale = await Locale.objects.first()
    assert locale is not None
    home = await ensure_root_page(locale)

    create_about = await client.post(
        f"/admin/pages/add/?parent={home.id}",
        data={
            "title": "About",
            "slug": "about",
            "live": "1",
            "show_in_menus": "1",
        },
        cookies=client.cookies,
        follow_redirects=False,
    )
    assert create_about.status_code == 303

    about = await Page.objects.filter(slug="about", locale_id=locale.id).first()
    assert about is not None
    assert about.parent_id == home.id
    assert about.path == "/about/"

    assert await get_page_public_url(about) == "/about/"
    assert (await client.get("/about/")).status_code == 200


@pytest.mark.asyncio
async def test_pages_explorer_adds_under_site_root_not_tree_root(
    public_app_client: AsyncClient,
) -> None:
    """Adding from /admin/pages/ must attach to the site homepage, not a sibling tree node."""

    client = public_app_client
    await _login(client)

    locale = await Locale.objects.first()
    assert locale is not None
    default_home = await ensure_root_page(locale)
    tree_root = await ensure_tree_root(locale)

    create_about = await client.post(
        "/admin/pages/add/",
        data={
            "title": "About",
            "slug": "about",
            "live": "1",
            "show_in_menus": "1",
        },
        cookies=client.cookies,
        follow_redirects=False,
    )
    assert create_about.status_code == 303

    about = await Page.objects.filter(slug="about", locale_id=locale.id).first()
    assert about is not None
    assert about.parent_id == default_home.id
    assert about.parent_id != tree_root.id
    assert about.path == "/about/"
    assert (await client.get("/about/")).status_code == 200


@pytest.mark.asyncio
async def test_upgrade_all_locales_repaths_stale_child_paths(tmp_path: Path) -> None:
    """Startup hook must fix /home/about/ leftovers even when the homepage is already at /."""

    database_url = f"sqlite:////{tmp_path / 'repath.db'}"
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
        from ragtail.pages import create_page
        from ragtail.sites import set_site_root_page

        tree_root = await ensure_tree_root(en)
        site = await ensure_default_site()
        home = await create_page(title="Home", slug="home", parent=tree_root, locale=en, live=True)
        about = await create_page(title="About", slug="about", parent=home, locale=en, live=True)
        await set_site_root_page(site, home)

        about.path = "/home/about/"
        await about.save()

        await upgrade_all_locales()

        about = await Page.objects.get(id=about.id)
        assert about.path == "/about/"

        route = await resolve_route("/about/")
        assert route is not None
        assert route.page.slug == "about"
        assert route.public_path == "/about/"
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_move_page_to_alternate_tree_and_back(public_app_client: AsyncClient) -> None:
    """Pages can be moved to a sibling page tree under the technical tree root."""

    client = public_app_client
    await _login(client)

    locale = await Locale.objects.first()
    assert locale is not None
    tree_root = await ensure_tree_root(locale)
    assert tree_root.id is not None

    default_home = await ensure_root_page(locale)

    create_about = await client.post(
        f"/admin/pages/add/?parent={default_home.id}",
        data={"title": "About", "slug": "about", "live": "1"},
        cookies=client.cookies,
        follow_redirects=False,
    )
    assert create_about.status_code == 303
    about = await Page.objects.filter(slug="about", locale_id=locale.id).first()
    assert about is not None
    assert about.path == "/about/"

    create_alt_home = await client.post(
        f"/admin/pages/add/?parent={tree_root.id}",
        data={"title": "Landing", "slug": "landing", "live": "1"},
        cookies=client.cookies,
        follow_redirects=False,
    )
    assert create_alt_home.status_code == 303
    alt_home = await Page.objects.filter(slug="landing", locale_id=locale.id).first()
    assert alt_home is not None
    assert alt_home.parent_id == tree_root.id

    move_to_alt = await client.post(
        f"/admin/pages/{about.id}/move/",
        data={"new_parent_id": str(alt_home.id)},
        cookies=client.cookies,
        follow_redirects=False,
    )
    assert move_to_alt.status_code == 303
    assert move_to_alt.headers["location"] == f"/admin/pages/{alt_home.id}/"

    about = await Page.objects.get(id=about.id)
    assert about.parent_id == alt_home.id
    assert about.path == "/landing/about/"
    assert await get_page_public_url(about) is None

    move_back = await client.post(
        f"/admin/pages/{about.id}/move/",
        data={"new_parent_id": str(default_home.id)},
        cookies=client.cookies,
        follow_redirects=False,
    )
    assert move_back.status_code == 303

    about = await Page.objects.get(id=about.id)
    assert about.parent_id == default_home.id
    assert about.path == "/about/"
    assert await get_page_public_url(about) == "/about/"
    assert (await client.get("/about/")).status_code == 200


@pytest.mark.asyncio
async def test_move_page_cannot_move_under_descendant(public_app_client: AsyncClient) -> None:
    client = public_app_client
    await _login(client)

    locale = await Locale.objects.first()
    assert locale is not None
    home = await ensure_root_page(locale)

    create_section = await client.post(
        f"/admin/pages/add/?parent={home.id}",
        data={"title": "Section", "slug": "section", "live": "1"},
        cookies=client.cookies,
        follow_redirects=False,
    )
    assert create_section.status_code == 303
    section = await Page.objects.filter(slug="section", locale_id=locale.id).first()
    assert section is not None

    response = await client.post(
        f"/admin/pages/{home.id}/move/",
        data={"new_parent_id": str(section.id)},
        cookies=client.cookies,
    )
    assert response.status_code == 200
    assert "cannot be moved under one of its descendants" in response.text
