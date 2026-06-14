from pathlib import Path

import pytest
import pytest_asyncio
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient
from oxyde import Field, db

from oxytail.auth import ensure_superuser
from oxytail.cms import FastAPICMS
from oxytail.db import run_migrations
from oxytail.models import Locale, Page
from oxytail.page_types import (
    cast_page,
    class_to_content_type,
    clear_page_models,
    content_type_to_component_name,
    get_page_model,
    register_page_model,
)
from oxytail.pages import create_page
from oxytail.routing import RouteMatch
from oxytail.templates import PyJsxRenderer, clear_pyjsx_components, register_pyjsx_component
from oxytail.wagtail_admin.services import ensure_root_page


def test_class_to_content_type() -> None:
    assert class_to_content_type("ContentPage") == "content_page"
    assert class_to_content_type("AboutPage") == "about_page"


def test_content_type_to_component_name() -> None:
    assert content_type_to_component_name("content_page") == "contentPage"


def test_register_page_model() -> None:
    clear_page_models()

    @register_page_model
    class StoryPage(Page):
        intro: str | None = Field(default=None)

    assert get_page_model("story_page") is StoryPage
    clear_page_models()


@pytest.mark.asyncio
async def test_pyjsx_renderer_serves_component() -> None:
    clear_page_models()
    clear_pyjsx_components()

    @register_page_model
    class TestPage(Page):
        note: str | None = Field(default=None)

        async def get_context(self, request, route):
            return {"tag": "hello"}

    def testPage(*, page, context):
        return f"<h1>{page.title}</h1><p>{context.get('tag')}</p>"

    register_pyjsx_component("test_page", testPage)

    page = TestPage(title="Hello", slug="hello", path="/hello/", content_type="test_page")
    locale = Locale(language_code="en", display_name="English")
    route = RouteMatch(page=page, locale=locale, path="/hello/", public_path="/hello/")

    engine = PyJsxRenderer()
    html = await engine.serve(Request({"type": "http"}), route)
    assert html == "<h1>Hello</h1><p>hello</p>"

    clear_page_models()
    clear_pyjsx_components()


@pytest.mark.asyncio
async def test_jinja2_renderer_serves_template(tmp_path: Path) -> None:
    clear_page_models()
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    (template_dir / "story_page.html").write_text(
        "<h1>{{ page.title }}</h1><p>{{ note }}</p>",
        encoding="utf-8",
    )

    @register_page_model
    class StoryPage(Page):
        note: str | None = Field(default=None)

        async def get_context(self, request, route):
            return {"note": "from-context"}

    from oxytail.templates import Jinja2Renderer

    page = StoryPage(title="Story", slug="story", path="/story/", content_type="story_page")
    locale = Locale(language_code="en", display_name="English")
    route = RouteMatch(page=page, locale=locale, path="/story/", public_path="/story/")

    engine = Jinja2Renderer(template_dir)
    html = await engine.serve(Request({"type": "http", "path": "/"}), route)
    assert html == "<h1>Story</h1><p>from-context</p>"

    clear_page_models()


@pytest_asyncio.fixture
async def html_client(tmp_path: Path):
    clear_page_models()
    clear_pyjsx_components()
    database_url = f"sqlite:////{tmp_path / 'template-engine.db'}"

    @register_page_model
    class SimplePage(Page):
        pass

    def simplePage(*, page, context):
        return f"<title>{page.title}</title>"

    register_pyjsx_component("simple_page", simplePage)

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
            page_model=SimplePage,
        )

        cms = FastAPICMS(
            secret_key="test-secret",
            template_engine=PyJsxRenderer(),
        )
        app = FastAPI(lifespan=cms.lifespan(database_url))
        cms.mount(app)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as http_client:
            yield http_client
    finally:
        await db.close()
        clear_page_models()
        clear_pyjsx_components()


@pytest.mark.asyncio
async def test_fastapi_cms_template_engine_renders_html(html_client: AsyncClient) -> None:
    response = await html_client.get("/about/")
    assert response.status_code == 200
    assert response.text == "<title>About</title>"
