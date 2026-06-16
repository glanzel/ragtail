from pathlib import Path

import pytest
import pytest_asyncio
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient
from oxyde import db

from ragtail.auth import ensure_superuser
from ragtail.cms import FastAPICMS
from ragtail.db import run_migrations
from ragtail.models import Locale, Page
from ragtail.pages import create_page
from ragtail.routing import RouteMatch
from ragtail.templates import (
    Jinja2Renderer,
    PageView,
    PyJsxRenderer,
    clear_page_views,
    clear_pyjsx_components,
    content_type_to_component_name,
    get_page_view,
    register_page_view,
    register_pyjsx_component,
)
from ragtail.wagtail_admin.services import ensure_root_page


def test_content_type_to_component_name() -> None:
    assert content_type_to_component_name("page") == "page"
    assert content_type_to_component_name("detail_page") == "detailPage"


def test_page_view_registry_fallback() -> None:
    clear_page_views()
    view = get_page_view("unknown_type")
    assert isinstance(view, PageView)


def test_register_page_view() -> None:
    clear_page_views()

    @register_page_view
    class CustomPageView(PageView):
        content_type = "custom"

        async def get_context(self, request, page, route):
            return {"extra": "value"}

    view = get_page_view("custom")
    assert isinstance(view, CustomPageView)


@pytest.mark.asyncio
async def test_pyjsx_renderer_serves_component() -> None:
    clear_pyjsx_components()

    def testPage(*, page, context):
        return f"<h1>{page.title}</h1><p>{context.get('tag')}</p>"

    register_pyjsx_component("test", testPage)

    @register_page_view
    class TestPageView(PageView):
        content_type = "test"

        async def get_context(self, request, page, route):
            return {"tag": "hello"}

    page = Page(title="Hello", slug="hello", path="/hello/", content_type="test")
    locale = Locale(language_code="en", display_name="English")
    route = RouteMatch(page=page, locale=locale, path="/hello/", public_path="/hello/")

    engine = PyJsxRenderer()
    html = await engine.serve(Request({"type": "http"}), route)
    assert html == "<h1>Hello</h1><p>hello</p>"

    clear_page_views()
    clear_pyjsx_components()


@pytest.mark.asyncio
async def test_jinja2_renderer_serves_template(tmp_path: Path) -> None:
    clear_page_views()
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    (template_dir / "story.html").write_text(
        "<h1>{{ page.title }}</h1><p>{{ note }}</p>",
        encoding="utf-8",
    )

    @register_page_view
    class StoryPageView(PageView):
        content_type = "story"

        async def get_context(self, request, page, route):
            return {"note": "from-context"}

        def get_template_name(self, request, page, route):
            return "story.html"

    page = Page(title="Story", slug="story", path="/story/", content_type="story")
    locale = Locale(language_code="en", display_name="English")
    route = RouteMatch(page=page, locale=locale, path="/story/", public_path="/story/")

    engine = Jinja2Renderer(template_dir)
    html = await engine.serve(Request({"type": "http", "path": "/"}), route)
    assert html == "<h1>Story</h1><p>from-context</p>"

    clear_page_views()


@pytest_asyncio.fixture
async def html_client(tmp_path: Path):
    clear_page_views()
    clear_pyjsx_components()
    database_url = f"sqlite:////{tmp_path / 'template-engine.db'}"

    def pageComponent(*, page, context):
        return f"<title>{page.title}</title>"

    register_pyjsx_component("page", pageComponent)

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
        clear_page_views()
        clear_pyjsx_components()


@pytest.mark.asyncio
async def test_fastapi_cms_template_engine_renders_html(html_client: AsyncClient) -> None:
    response = await html_client.get("/about/")
    assert response.status_code == 200
    assert response.text == "<title>About</title>"
