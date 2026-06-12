from pathlib import Path

import pytest
import pytest_asyncio
from oxyde import db

from oxytail.db import ensure_tables, run_migrations
from oxytail.models import User


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

    assert applied == ["0001_initial"]
    assert await User.objects.first() is None


@pytest.mark.asyncio
async def test_run_migrations_is_idempotent(database):
    first = await run_migrations(database)
    second = await run_migrations(database)

    assert first == ["0001_initial"]
    assert second == []


@pytest.mark.asyncio
async def test_ensure_tables_applies_migrations(database):
    applied = await ensure_tables(database)

    assert applied == ["0001_initial"]
