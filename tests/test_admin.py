from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from oxyde import db

from ragtail.auth import ensure_superuser
from ragtail.db import run_migrations
from ragtail.fastapi import create_app
from ragtail.models import Locale
from ragtail.page_types import clear_page_models
from ragtail.pages import create_page
from ragtail.wagtail_admin.services import ensure_root_page


@pytest_asyncio.fixture
async def client(tmp_path: Path):
    import importlib
    import sys

    clear_page_models()
    demo_dir = Path(__file__).resolve().parents[1] / "examples" / "demo"
    sys.path.insert(0, str(demo_dir))
    if "pages" in sys.modules:
        importlib.reload(sys.modules["pages"])
    else:
        import pages  # noqa: F401

    database_url = f"sqlite:////{tmp_path / 'admin.db'}"
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
        clear_page_models()


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
async def test_admin_page_add_persists_typed_extra_field(client: AsyncClient) -> None:
    from oxyde import Field

    from ragtail.models import Page
    from ragtail.page_types import cast_page, clear_page_models, get_page_model, register_page_model

    clear_page_models()

    @register_page_model
    class BlogPage(Page):
        intro: str | None = Field(default=None)

    login = await client.post(
        "/admin/login/",
        data={"username": "admin", "password": "admin", "next": "/admin/pages/"},
        follow_redirects=False,
    )
    pages = await client.get("/admin/pages/", cookies=login.cookies, follow_redirects=False)
    root_id = pages.headers["location"].rstrip("/").rsplit("/", 1)[-1]

    create = await client.post(
        f"/admin/pages/add/?parent={root_id}",
        data={
            "content_type": "blog_page",
            "title": "Blog post",
            "slug": "blog-post",
            "intro": "Short intro text",
            "live": "1",
        },
        cookies=login.cookies,
        follow_redirects=False,
    )
    assert create.status_code == 303

    stored = await Page.objects.filter(slug="blog-post").first()
    assert stored is not None
    typed = await cast_page(stored)
    assert get_page_model("blog_page") is BlogPage
    assert typed.intro == "Short intro text"

    clear_page_models()


@pytest.mark.asyncio
async def test_admin_page_edit_persists_typed_extra_field(client: AsyncClient) -> None:
    from oxyde import Field

    from ragtail.models import Page
    from ragtail.page_types import cast_page, clear_page_models, register_page_model

    clear_page_models()

    @register_page_model
    class BlogPage(Page):
        intro: str | None = Field(default=None)

    login = await client.post(
        "/admin/login/",
        data={"username": "admin", "password": "admin", "next": "/admin/pages/"},
        follow_redirects=False,
    )
    pages = await client.get("/admin/pages/", cookies=login.cookies, follow_redirects=False)
    root_id = pages.headers["location"].rstrip("/").rsplit("/", 1)[-1]

    create = await client.post(
        f"/admin/pages/add/?parent={root_id}",
        data={
            "content_type": "blog_page",
            "title": "Blog post",
            "slug": "blog-post",
            "intro": "First intro",
            "live": "1",
        },
        cookies=login.cookies,
        follow_redirects=False,
    )
    assert create.status_code == 303
    stored = await Page.objects.filter(slug="blog-post").first()
    assert stored is not None

    edit = await client.post(
        f"/admin/pages/{stored.id}/edit/",
        data={
            "title": "Blog post",
            "slug": "blog-post",
            "intro": "Updated intro",
            "live": "1",
        },
        cookies=login.cookies,
        follow_redirects=False,
    )
    assert edit.status_code == 303
    typed = await cast_page(await Page.objects.get(id=stored.id))
    assert typed.intro == "Updated intro"

    clear_page_models()


@pytest.mark.asyncio
async def test_admin_page_edit_body_uses_base64_initial_value(client: AsyncClient) -> None:
    import re

    from ragtail.models import Page
    from ragtail.page_types import cast_page

    about_page = await cast_page(await Page.objects.filter(slug="about").first())
    assert about_page is not None
    about_page.body = "# Title\n\nParagraph with **bold**"
    await about_page.save()

    login = await client.post(
        "/admin/login/",
        data={"username": "admin", "password": "admin", "next": "/admin/pages/"},
        follow_redirects=False,
    )

    edit = await client.get(f"/admin/pages/{about_page.id}/edit/", cookies=login.cookies)
    assert edit.status_code == 200
    assert "data-initial-b64=" in edit.text
    textarea_match = re.search(
        r'<textarea[^>]*name="body"[^>]*>(.*?)</textarea>',
        edit.text,
        re.DOTALL,
    )
    assert textarea_match is not None
    assert textarea_match.group(1).strip() == ""


@pytest.mark.asyncio
async def test_admin_page_edit_includes_richtext_editor(client: AsyncClient) -> None:
    from ragtail.models import Page
    from ragtail.page_types import cast_page

    login = await client.post(
        "/admin/login/",
        data={"username": "admin", "password": "admin", "next": "/admin/pages/"},
        follow_redirects=False,
    )
    about_page = await cast_page(await Page.objects.filter(slug="about").first())
    assert about_page is not None

    edit = await client.get(f"/admin/pages/{about_page.id}/edit/", cookies=login.cookies)
    assert edit.status_code == 200
    assert "data-richtext-toolbar" in edit.text
    assert "data-richtext-mount" in edit.text
    assert "richtext-toolbar-btn" in edit.text
    assert edit.text.count('data-action="') >= 9
    assert "richtext.js" in edit.text


@pytest.mark.asyncio
async def test_admin_page_explorer_has_locale_switcher(client: AsyncClient) -> None:
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
    assert 'id="id_explorer_locale"' in listing.text
    assert "Deutsch" in listing.text
    assert "About" in listing.text

    switch = await client.post(
        "/admin/set-locale/",
        data={"language_code": "de", "next": f"/admin/pages/{root_id}/"},
        cookies=login.cookies,
        follow_redirects=False,
    )
    assert switch.status_code == 303


@pytest.mark.asyncio
async def test_admin_translate_page(client: AsyncClient) -> None:
    from ragtail.models import Locale, Page

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
    en = await Locale.objects.get_or_none(language_code="en")
    de = await Locale.objects.get_or_none(language_code="de")
    about = await Page.objects.filter(slug="about").first()
    assert en is not None and de is not None and about is not None

    form = await client.get(
        f"/admin/pages/{about.id}/translate/?language_code=de",
        cookies=login.cookies,
    )
    assert form.status_code == 200
    assert "Translate" in form.text

    create = await client.post(
        f"/admin/pages/{about.id}/translate/?language_code=de",
        data={"title": "Ueber uns", "slug": "ueber-uns", "live": "1"},
        cookies=login.cookies,
        follow_redirects=False,
    )
    assert create.status_code == 303

    translated = await Page.objects.filter(translation_key=about.translation_key, locale_id=de.id).first()
    assert translated is not None
    assert translated.slug == "ueber-uns"
