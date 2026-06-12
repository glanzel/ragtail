from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from oxyde import db

from oxytail.auth import ensure_superuser, verify_password
from oxytail.db import run_migrations
from oxytail.fastapi import create_app
from oxytail.models import Locale, User
from oxytail.wagtail_admin.services import ensure_root_page

@pytest_asyncio.fixture
async def client(tmp_path: Path):
    database_url = f"sqlite:////{tmp_path / 'admin-users.db'}"
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
        await ensure_root_page(en)

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


async def _login(client: AsyncClient) -> None:
    response = await client.post(
        "/admin/login/",
        data={"username": "admin", "password": "admin", "next": "/admin/"},
        follow_redirects=False,
    )
    assert response.status_code == 303


@pytest.mark.asyncio
async def test_users_list_requires_login(client: AsyncClient) -> None:
    response = await client.get("/admin/users/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"].startswith("/admin/login/")


@pytest.mark.asyncio
async def test_create_and_list_users(client: AsyncClient) -> None:
    await _login(client)
    listing = await client.get("/admin/users/", cookies=client.cookies)
    assert listing.status_code == 200
    assert "Add user" in listing.text

    create = await client.post(
        "/admin/users/add/",
        data={
            "username": "editor",
            "email": "editor@example.com",
            "password": "editor-pass",
            "is_staff": "1",
            "is_active": "1",
        },
        cookies=client.cookies,
        follow_redirects=False,
    )
    assert create.status_code == 303
    assert create.headers["location"] == "/admin/users/"

    editor = await User.objects.get_or_none(username="editor")
    assert editor is not None
    assert editor.is_staff is True
    assert verify_password("editor-pass", editor.password_hash)


@pytest.mark.asyncio
async def test_admin_reset_user_password(client: AsyncClient) -> None:
    await _login(client)
    await client.post(
        "/admin/users/add/",
        data={
            "username": "editor",
            "email": "editor@example.com",
            "password": "old-pass",
            "is_staff": "1",
            "is_active": "1",
        },
        cookies=client.cookies,
        follow_redirects=False,
    )
    editor = await User.objects.get_or_none(username="editor")
    assert editor is not None

    reset = await client.post(
        f"/admin/users/{editor.id}/reset-password/",
        data={
            "password": "new-pass",
            "password_confirm": "new-pass",
        },
        cookies=client.cookies,
    )
    assert reset.status_code == 200
    assert "has been reset" in reset.text

    updated = await User.objects.get_or_none(id=editor.id)
    assert updated is not None
    assert verify_password("new-pass", updated.password_hash)


@pytest.mark.asyncio
async def test_change_own_password(client: AsyncClient) -> None:
    await _login(client)
    response = await client.post(
        "/admin/account/password/",
        data={
            "current_password": "admin",
            "password": "admin-new",
            "password_confirm": "admin-new",
        },
        cookies=client.cookies,
    )
    assert response.status_code == 200
    assert "has been changed" in response.text

    admin = await User.objects.get_or_none(username="admin")
    assert admin is not None
    assert verify_password("admin-new", admin.password_hash)

    relogin = await client.post(
        "/admin/login/",
        data={"username": "admin", "password": "admin-new", "next": "/admin/"},
        follow_redirects=False,
    )
    assert relogin.status_code == 303


@pytest.mark.asyncio
async def test_edit_user_email(client: AsyncClient) -> None:
    await _login(client)
    editor = await User.objects.get_or_none(username="editor")
    if editor is None:
        await client.post(
            "/admin/users/add/",
            data={
                "username": "editor",
                "email": "editor@example.com",
                "password": "editor-pass",
                "is_staff": "1",
                "is_active": "1",
            },
            cookies=client.cookies,
            follow_redirects=False,
        )
        editor = await User.objects.get_or_none(username="editor")
    assert editor is not None

    edit = await client.post(
        f"/admin/users/{editor.id}/edit/",
        data={
            "email": "editor.new@example.com",
            "is_staff": "1",
            "is_active": "1",
        },
        cookies=client.cookies,
        follow_redirects=False,
    )
    assert edit.status_code == 303

    updated = await User.objects.get_or_none(id=editor.id)
    assert updated is not None
    assert updated.email == "editor.new@example.com"


@pytest.mark.asyncio
async def test_forgot_password_page_is_public(client: AsyncClient) -> None:
    response = await client.get("/admin/password-reset/")
    assert response.status_code == 200
    assert "Self-service password reset is not available" in response.text


@pytest.mark.asyncio
async def test_cannot_delete_self(client: AsyncClient) -> None:
    await _login(client)
    admin = await User.objects.get_or_none(username="admin")
    assert admin is not None

    response = await client.post(
        f"/admin/users/{admin.id}/delete/",
        cookies=client.cookies,
    )
    assert response.status_code == 200
    assert "cannot delete your own account" in response.text.lower()
