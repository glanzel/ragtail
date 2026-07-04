from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from oxyde import db
from fastapi.responses import HTMLResponse

from ragtail.auth import ensure_superuser
from ragtail.db import run_migrations
from ragtail.fastapi import create_app
from ragtail.models import Locale, Page
from ragtail.pages import create_page
from ragtail.richtext import (
    prepare_body_for_storage,
    render_body,
    sanitize_stored_body,
)
from ragtail.seo import normalize_search_description, search_description_error
from ragtail.ragtail_admin.services import ensure_root_page


def test_render_body_converts_markdown_to_html() -> None:
    html = render_body("Hello **world**")
    assert "<strong>world</strong>" in html


def test_render_body_converts_markdown_links() -> None:
    html = render_body("Visit [our site](https://example.com) today.")
    assert '<a href="https://example.com">our site</a>' in html


def test_render_body_escapes_inline_html_in_markdown() -> None:
    html = render_body("**bold** and <em>not html</em>")
    assert "<strong>bold</strong>" in html
    assert "<em>" not in html
    assert "&lt;em&gt;" in html


def test_render_body_escapes_html_tags_in_markdown() -> None:
    html = render_body("<p>Hello</p>")
    assert "<p>Hello</p>" not in html
    assert "&lt;p&gt;" in html


def test_sanitize_stored_body_removes_script_but_keeps_markdown() -> None:
    body = "# Title\n\nHello **world**\n\n<script>alert(1)</script>"
    cleaned = sanitize_stored_body(body)
    assert cleaned.startswith("# Title")
    assert "**world**" in cleaned
    assert "<script" not in cleaned


def test_prepare_body_for_storage_is_one_to_one_for_safe_markdown() -> None:
    body = "## Heading\n\nParagraph with `code` and [link](https://example.com)."
    assert prepare_body_for_storage(body) == body


def test_prepare_body_for_storage_strips_trailing_line_whitespace() -> None:
    body = "## Heading   \n\nParagraph with trailing spaces.   \n"
    assert prepare_body_for_storage(body) == "## Heading\n\nParagraph with trailing spaces."


def test_prepare_body_for_storage_returns_none_for_empty() -> None:
    assert prepare_body_for_storage("") is None
    assert prepare_body_for_storage(None) is None


def test_normalize_search_description_strips_whitespace() -> None:
    assert normalize_search_description("   hello   ") == "hello"
    assert normalize_search_description("     ") is None


def test_search_description_error_for_too_long_value() -> None:
    assert search_description_error("x" * 501) is not None
    assert search_description_error("x" * 500) is None


@pytest_asyncio.fixture
async def public_client(tmp_path: Path, oxyde_config):
    from oxyde import Field

    from ragtail.page_types import clear_page_models, register_page_model

    clear_page_models()

    @register_page_model
    class ContentPage(Page):
        body: str | None = Field(default=None, db_type="TEXT")

    database_url = oxyde_config(f"sqlite:////{tmp_path / 'richtext.db'}")
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
            page_model=ContentPage,
            body="Placeholder",
        )

        async def render_page(_request, route):
            return HTMLResponse(render_body(route.page.body))

        app = create_app(
            mount_ragtail_admin=True,
            secret_key="test-secret",
            renderer=render_page,
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as http_client:
            yield http_client
    finally:
        await db.close()
        clear_page_models()


@pytest.mark.asyncio
async def test_public_page_renders_stored_markdown_links(public_client: AsyncClient) -> None:
    about_page = await Page.objects.filter(slug="about").first()
    assert about_page is not None
    about_page.body = "Read more on [our site](https://example.com)."
    await about_page.save()

    response = await public_client.get("/about/")
    assert response.status_code == 200
    assert '[our site](https://example.com)' not in response.text
    assert 'href="https://example.com"' in response.text
    assert ">our site</a>" in response.text


@pytest.mark.asyncio
async def test_public_page_renders_stored_markdown_as_html(public_client: AsyncClient) -> None:
    about_page = await Page.objects.filter(slug="about").first()
    assert about_page is not None
    about_page.body = "Hello **world**"
    await about_page.save()

    response = await public_client.get("/about/")
    assert response.status_code == 200
    assert "**world**" not in response.text
    assert "<strong>world</strong>" in response.text


@pytest.mark.asyncio
async def test_admin_save_persists_markdown_body(public_client: AsyncClient) -> None:
    from ragtail.models import Page
    from ragtail.page_types import cast_page

    login = await public_client.post(
        "/admin/login/",
        data={"username": "admin", "password": "admin", "next": "/admin/pages/"},
        follow_redirects=False,
    )
    about_page = await Page.objects.filter(slug="about").first()
    assert about_page is not None

    await public_client.post(
        f"/admin/pages/{about_page.id}/edit/",
        data={
            "title": about_page.title,
            "slug": about_page.slug,
            "body": "## Heading\n\nSaved **markdown**.",
            "seo_title": "",
            "search_description": "",
            "live": "1",
        },
        cookies=login.cookies,
        follow_redirects=False,
    )

    saved = await Page.objects.get(id=about_page.id)
    assert saved.body is not None
    assert "## Heading" in saved.body
    assert "**markdown**" in saved.body

    response = await public_client.get("/about/")
    assert response.status_code == 200
    assert "**markdown**" not in response.text
    assert "<h2>Heading</h2>" in response.text
    assert "<strong>markdown</strong>" in response.text
