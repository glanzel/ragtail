from pathlib import Path

import pytest
import pytest_asyncio
from oxyde import db
from oxyde.migrations.tracker import ensure_migrations_table, record_migration

from ragtail.db import ragtail_migrations_dir, resolve_migrations_dir, run_migrations
from ragtail.models import User


def test_ragtail_migrations_dir_points_at_package() -> None:
    path = ragtail_migrations_dir()
    assert path.name == "migrations"
    assert path.parent.name == "ragtail"
    assert (path / "0001_ragtail_initial.py").is_file()


def test_resolve_migrations_dir_ignores_host_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    host_migrations = tmp_path / "migrations"
    host_migrations.mkdir()
    (host_migrations / "0001_create_products.py").write_text(
        "depends_on=None\ndef upgrade(ctx): pass\ndef downgrade(ctx): pass\n"
    )
    monkeypatch.chdir(tmp_path)
    assert resolve_migrations_dir() == ragtail_migrations_dir()


@pytest_asyncio.fixture
async def database(tmp_path: Path):
    database_url = f"sqlite:////{tmp_path / 'migrations.db'}"
    await db.init(default=database_url)
    try:
        yield await db.get_connection("default")
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_run_migrations_creates_tables(database):
    applied = await run_migrations(database)

    assert applied == ["0001_ragtail_initial", "0002_page_data", "0003_sites", "0004_images"]
    assert await User.objects.first() is None


@pytest.mark.asyncio
async def test_run_migrations_is_idempotent(database):
    first = await run_migrations(database)
    second = await run_migrations(database)

    assert first == ["0001_ragtail_initial", "0002_page_data", "0003_sites", "0004_images"]
    assert second == []


@pytest.mark.asyncio
async def test_run_migrations_not_blocked_by_host_0001_initial(database) -> None:
    await ensure_migrations_table("default")
    await record_migration("0001_initial", "default")

    applied = await run_migrations(database)

    assert applied == ["0001_ragtail_initial", "0002_page_data", "0003_sites", "0004_images"]
    assert await User.objects.first() is None
