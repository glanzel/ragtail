from pathlib import Path

import pytest
from oxyde import db

from ragtail.db import run_migrations
from ragtail.models import Locale, Page
from ragtail.pages import create_page, create_translation
from ragtail.routing import resolve_route
from ragtail.ragtail_admin.services import ensure_root_page
from ragtail.sites import ensure_default_site, ensure_tree_root, set_site_root_page


@pytest.mark.asyncio
async def test_homepage_uses_site_root_translation(tmp_path: Path) -> None:
    database_url = f"sqlite:////{tmp_path / 'site-routing.db'}"
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

        root_route = await resolve_route("/")
        assert root_route is not None
        assert root_route.page.id == home.id

        de_root_route = await resolve_route("/de/")
        assert de_root_route is not None
        assert de_root_route.page.id == de_home.id
        assert de_root_route.page.title == "Zuhause"
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_nested_section_keeps_slug_prefix(tmp_path: Path) -> None:
    database_url = f"sqlite:////{tmp_path / 'blog-section.db'}"
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
        home = await ensure_root_page(en)
        blog = await create_page(
            title="Blog",
            slug="blog",
            parent=home,
            locale=en,
            live=True,
        )
        post = await create_page(
            title="First post",
            slug="first-post",
            parent=blog,
            locale=en,
            live=True,
        )

        assert home.path == "/"
        assert blog.path == "/blog/"
        assert post.path == "/blog/first-post/"

        route = await resolve_route("/blog/first-post/")
        assert route is not None
        assert route.page.id == post.id
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_tree_routing_resolves_about_when_stored_path_is_wrong(tmp_path: Path) -> None:
    database_url = f"sqlite:////{tmp_path / 'tree-routing.db'}"
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
        tree_root = await ensure_tree_root(en)
        site = await ensure_default_site()
        home = await create_page(
            title="Home",
            slug="home",
            parent=tree_root,
            locale=en,
            live=True,
        )
        about = await create_page(
            title="About",
            slug="about",
            parent=home,
            locale=en,
            live=True,
        )
        await set_site_root_page(site, home)

        about.path = "/home/about/"
        await about.save()

        route = await resolve_route("/about/")
        assert route is not None
        assert route.page.id == about.id
        assert route.public_path == "/about/"
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_prefix_default_language_from_site(tmp_path: Path) -> None:
    database_url = f"sqlite:////{tmp_path / 'site-prefix.db'}"
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
        home = await ensure_root_page(en)
        site = await ensure_default_site()
        await set_site_root_page(site, home)
        site.prefix_default_language = True
        await site.save()

        route = await resolve_route("/")
        assert route is not None
        assert route.public_path == "/en/"
    finally:
        await db.close()
