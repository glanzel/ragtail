from __future__ import annotations

import io
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from oxyde import Field, db

from ragtail.db import run_migrations
from ragtail.fastapi import create_app
from ragtail.images import Image, ImageField, configure_media, reset_media_config, reset_storage
from ragtail.images.renditions import generate_rendition_bytes
from ragtail.images.upload import create_image_from_upload, update_image_focal_point
from ragtail.models import Locale, Page
from ragtail.page_types import cast_page, clear_page_models, persist_page, register_page_model
from ragtail.pages import create_page
from ragtail.ragtail_admin.services import ensure_root_page
from ragtail.templates import Jinja2Renderer


def _make_png(width: int, height: int, *, color: tuple[int, int, int] = (200, 100, 50)) -> bytes:
    from PIL import Image as PILImage

    image = PILImage.new("RGB", (width, height), color)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest_asyncio.fixture
async def media_env(tmp_path: Path, oxyde_config):
    media_root = tmp_path / "media"
    configure_media(root=media_root, url="/media/")
    await db.init(default=oxyde_config(f"sqlite:////{tmp_path / 'images.db'}"))
    connection = await db.get_connection("default")
    await run_migrations(connection)
    yield media_root
    await db.close()
    reset_storage()
    reset_media_config()


@pytest.mark.asyncio
async def test_create_image_and_dimensions(media_env: Path) -> None:
    data = _make_png(800, 600)
    image = await create_image_from_upload(title="Test", filename="test.png", data=data)
    assert image.id is not None
    assert image.width == 800
    assert image.height == 600
    assert image.url.startswith("/media/")
    assert (media_env / image.file).is_file()


@pytest.mark.asyncio
async def test_rendition_cache_and_fill(media_env: Path) -> None:
    data = _make_png(1200, 600)
    image = await create_image_from_upload(title="Wide", filename="wide.png", data=data)
    await update_image_focal_point(image, x=0.75, y=0.5)

    first = await image.get_rendition("fill-400x400")
    second = await image.get_rendition("fill-400x400")
    assert first.id == second.id
    assert first.width == 400
    assert first.height == 400
    assert first.url.endswith(".fill-400x400.png") or ".fill-400x400." in first.file


@pytest.mark.asyncio
async def test_focal_point_invalidates_renditions(media_env: Path) -> None:
    from ragtail.images.models import Rendition

    data = _make_png(600, 400)
    image = await create_image_from_upload(title="Invalidate", filename="inv.png", data=data)
    rendition = await image.get_rendition("width-200")
    old_id = rendition.id

    await update_image_focal_point(image, x=0.2, y=0.8)
    remaining = await Rendition.objects.filter(image_id=image.id).all()
    assert all(item.id != old_id for item in remaining)


@pytest.mark.asyncio
async def test_imagefield_roundtrip(media_env: Path) -> None:
    @register_page_model
    class HeroPage(Page):
        hero_image: Image | None = ImageField(default=None)

    try:
        en = await Locale.objects.create(
            language_code="en",
            display_name="English",
            is_default=True,
            is_active=True,
        )
        home = await ensure_root_page(en)
        image = await create_image_from_upload(title="Hero", filename="hero.png", data=_make_png(300, 200))

        page = await create_page(
            title="Hero page",
            slug="hero-page",
            parent=home,
            locale=en,
            live=True,
            page_model=HeroPage,
            hero_image=image,
        )
        loaded = await cast_page(await Page.objects.get(id=page.id))
        assert isinstance(loaded, HeroPage)
        assert loaded.hero_image is not None
        assert loaded.hero_image.id == image.id
        assert loaded.hero_image.title == "Hero"
    finally:
        clear_page_models()


@pytest.mark.asyncio
async def test_admin_image_edit_includes_focal_point(media_env: Path) -> None:
    clear_page_models()

    @register_page_model
    class ContentPage(Page):
        body: str | None = Field(default=None, db_type="TEXT")

    try:
        from ragtail.auth import ensure_superuser

        await ensure_superuser(username="admin", password="admin")
        en = await Locale.objects.create(
            language_code="en",
            display_name="English",
            is_default=True,
            is_active=True,
        )
        await ensure_root_page(en)
        image = await create_image_from_upload(
            title="Focal",
            filename="focal.png",
            data=_make_png(320, 240),
        )

        app = create_app(
            mount_ragtail_admin=True,
            secret_key="test-secret",
            media_root=str(media_env),
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post(
                "/admin/login/",
                data={"username": "admin", "password": "admin"},
                follow_redirects=False,
            )
            page = await client.get(f"/admin/images/{image.id}/edit/")
            assert page.status_code == 200
            assert "ragtail-focal-marker" in page.text
            assert "focal-point.css" in page.text
            assert "focal-point.js" in page.text
            assert 'name="focal_point_x"' in page.text

            save = await client.post(
                f"/admin/images/{image.id}/edit/",
                data={
                    "title": "Focal updated",
                    "focal_point_x": "0.25",
                    "focal_point_y": "0.75",
                },
                follow_redirects=False,
            )
            assert save.status_code == 303

            updated = await Image.objects.get(id=image.id)
            assert updated.title == "Focal updated"
            assert updated.focal_point_x == pytest.approx(0.25)
            assert updated.focal_point_y == pytest.approx(0.75)

            legacy = await client.get(
                f"/admin/images/{image.id}/focal-point/",
                follow_redirects=False,
            )
            assert legacy.status_code == 303
            assert legacy.headers["location"].endswith(f"/admin/images/{image.id}/edit/")
    finally:
        clear_page_models()


@pytest.mark.asyncio
async def test_media_served_with_pages_router(media_env: Path) -> None:
    data = _make_png(120, 90)
    image = await create_image_from_upload(title="Serve", filename="serve.png", data=data)
    clear_page_models()

    @register_page_model
    class ContentPage(Page):
        body: str | None = Field(default=None, db_type="TEXT")

    try:
        en = await Locale.objects.create(
            language_code="en",
            display_name="English",
            is_default=True,
            is_active=True,
        )
        await ensure_root_page(en)

        app = create_app(
            mount_ragtail_admin=True,
            secret_key="test-secret",
            media_root=str(media_env),
            pages=True,
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(image.url)
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("image/")
    finally:
        clear_page_models()


@pytest.mark.asyncio
async def test_image_update_after_reload(media_env: Path) -> None:
    data = _make_png(400, 300)
    image = await create_image_from_upload(title="Original", filename="orig.png", data=data)
    loaded = await Image.objects.get(id=image.id)
    loaded.title = "Renamed"
    await loaded.save()
    refreshed = await Image.objects.get(id=image.id)
    assert refreshed.title == "Renamed"


@pytest.mark.asyncio
async def test_admin_image_edit_save(media_env: Path) -> None:
    clear_page_models()

    @register_page_model
    class ContentPage(Page):
        body: str | None = Field(default=None, db_type="TEXT")

    try:
        from ragtail.auth import ensure_superuser

        await ensure_superuser(username="admin", password="admin")
        en = await Locale.objects.create(
            language_code="en",
            display_name="English",
            is_default=True,
            is_active=True,
        )
        await ensure_root_page(en)

        app = create_app(
            mount_ragtail_admin=True,
            secret_key="test-secret",
            media_root=str(media_env),
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            login = await client.post(
                "/admin/login/",
                data={"username": "admin", "password": "admin"},
                follow_redirects=False,
            )
            assert login.status_code == 303

            png = _make_png(100, 80)
            upload = await client.post(
                "/admin/images/upload/",
                data={"title": "Uploaded"},
                files={"file": ("upload.png", png, "image/png")},
                follow_redirects=False,
            )
            assert upload.status_code == 303, upload.text

            listing = await client.get("/admin/images/")
            assert listing.status_code == 200
            assert "Uploaded" in listing.text

            image = await Image.objects.order_by("-created_at").first()
            assert image is not None

            edit_get = await client.get(f"/admin/images/{image.id}/edit/")
            assert edit_get.status_code == 200
            assert 'src="/media/' in edit_get.text

            edit_post = await client.post(
                f"/admin/images/{image.id}/edit/",
                data={"title": "Updated title"},
                follow_redirects=False,
            )
            assert edit_post.status_code == 303

            updated = await Image.objects.get(id=image.id)
            assert updated.title == "Updated title"
    finally:
        clear_page_models()


@pytest.mark.asyncio
async def test_admin_image_upload_and_list(media_env: Path) -> None:
    clear_page_models()

    @register_page_model
    class ContentPage(Page):
        body: str | None = Field(default=None, db_type="TEXT")

    try:
        from ragtail.auth import ensure_superuser

        await ensure_superuser(username="admin", password="admin")
        en = await Locale.objects.create(
            language_code="en",
            display_name="English",
            is_default=True,
            is_active=True,
        )
        await ensure_root_page(en)

        app = create_app(
            mount_ragtail_admin=True,
            secret_key="test-secret",
            media_root=str(media_env),
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            login = await client.post(
                "/admin/login/",
                data={"username": "admin", "password": "admin"},
                follow_redirects=False,
            )
            assert login.status_code == 303

            png = _make_png(100, 80)
            upload = await client.post(
                "/admin/images/upload/",
                data={"title": "Uploaded"},
                files={"file": ("upload.png", png, "image/png")},
                follow_redirects=False,
            )
            assert upload.status_code == 303, upload.text

            listing = await client.get("/admin/images/")
            assert listing.status_code == 200
            assert "Uploaded" in listing.text
    finally:
        clear_page_models()


@pytest.mark.asyncio
async def test_jinja_rendition_filter(media_env: Path, tmp_path: Path) -> None:
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    (template_dir / "content_page.html").write_text(
        '{{ ragtail_image(page.hero_image, "width-200") }}',
        encoding="utf-8",
    )

    @register_page_model
    class ContentPage(Page):
        hero_image: Image | None = ImageField(default=None, renditions=("width-200",))

    image = await create_image_from_upload(title="Jinja", filename="jinja.png", data=_make_png(640, 480))
    page = ContentPage(
        title="Test",
        slug="test",
        path="/test/",
        depth=2,
        hero_image=image,
        content_type="content_page",
    )

    from ragtail.routing import RouteMatch

    route = RouteMatch(
        page=page,
        locale=Locale(language_code="en", display_name="English"),
        path="/test/",
        public_path="/test/",
        is_fallback=False,
    )

    renderer = Jinja2Renderer(template_dir)
    from fastapi import Request

    request = Request({"type": "http", "method": "GET", "path": "/test/", "headers": []})
    html = await renderer.serve(request, route)
    assert "width=\"200\"" in html
    assert "/media/" in html

    clear_page_models()


def test_image_field_control_includes_edit_link() -> None:
    from types import SimpleNamespace

    from ragtail.ragtail_admin.components.images import ImageFieldControl

    field = SimpleNamespace(name="hero_image", label="Hero image")
    html = str(
        ImageFieldControl(
            field_def=field,
            value="42",
            preview_url="/media/x.jpg",
            preview_title="Hero",
        )
    )
    assert 'href="/admin/images/42/edit/"' in html
    assert 'target="_blank"' in html
    assert "Edit image" in html
    assert 'id="edit_hero_image"' in html


def test_generate_rendition_bytes_max() -> None:
    data = _make_png(1000, 500)
    output, width, height, fmt = generate_rendition_bytes(data, filter_spec="max-200x200|format-png")
    assert fmt == "png"
    assert width <= 200
    assert height <= 200
    assert len(output) > 0
