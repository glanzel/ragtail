from pathlib import Path

import pytest
import pytest_asyncio
from oxyde import create_tables, db

from oxytail.db import ensure_tables
from oxytail.models import User


@pytest_asyncio.fixture
async def database(tmp_path: Path):
    database_url = f"sqlite:///{tmp_path / 'ensure_tables.db'}"
    await db.init(default=database_url)
    try:
        yield await db.get_connection("default")
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_ensure_tables_creates_missing_tables(database):
    await ensure_tables(database)

    assert await User.objects.first() is None


@pytest.mark.asyncio
async def test_ensure_tables_is_idempotent(database):
    await create_tables(database)
    await ensure_tables(database)
