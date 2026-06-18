from pathlib import Path

import pytest

from ragtail.db import init_database, prepare_sqlite_database, sqlite_database_path


def test_sqlite_database_path_relative_url() -> None:
    path = sqlite_database_path("sqlite://ragtail.db")
    assert path == Path.cwd() / "ragtail.db"


def test_prepare_sqlite_database_creates_parent_directory(tmp_path: Path) -> None:
    database_url = f"sqlite:////{tmp_path / 'nested' / 'ragtail.db'}"
    prepare_sqlite_database(database_url)
    assert (tmp_path / "nested").is_dir()


@pytest.mark.asyncio
async def test_init_database_creates_file_and_applies_migrations(tmp_path: Path) -> None:
    database_url = f"sqlite:////{tmp_path / 'nested' / 'fresh.db'}"
    applied = await init_database(database_url)
    assert applied == ["0001_ragtail_initial", "0002_page_data", "0003_sites"]
    assert (tmp_path / "nested" / "fresh.db").is_file()
