from pathlib import Path

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from oxyde import db

from ragtail.auth import ensure_superuser
from ragtail.cms import FastAPICMS
from ragtail.db import run_migrations
from ragtail.models import Locale
from ragtail.ragtail_admin.services import ensure_root_page


@pytest_asyncio.fixture
async def client(tmp_path: Path):
    database_url = f"sqlite:////{tmp_path / 'cms-mount.db'}"
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

        cms = FastAPICMS(secret_key="test-secret")
        app = FastAPI(lifespan=cms.lifespan(database_url))
        cms.mount(app)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as http_client:
            yield http_client
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_fastapi_cms_mount_serves_admin_login(client: AsyncClient) -> None:
    response = await client.get("/admin/login/")
    assert response.status_code == 200
    assert "Sign in to Ragtail" in response.text


@pytest.mark.asyncio
async def test_fastapi_cms_mount_serves_json_api(client: AsyncClient) -> None:
    response = await client.get("/api/cms/pages/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["title"]
    assert payload["path"] == "/"


@pytest.mark.asyncio
async def test_fastapi_cms_mount_admin_requires_login(client: AsyncClient) -> None:
    response = await client.get("/admin/pages/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"].startswith("/admin/login/")
