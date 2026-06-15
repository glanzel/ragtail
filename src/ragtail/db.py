from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import unquote, urlparse

from oxyde import db
from oxyde.migrations import apply_migrations

from oxyde.db.pool import AsyncDatabase


def resolve_migrations_dir() -> Path:
    """Return the directory containing numbered Oxyde migration files."""
    if configured := os.environ.get("RAGTAIL_MIGRATIONS_DIR"):
        return Path(configured)

    cwd_dir = Path.cwd() / "migrations"
    if any(cwd_dir.glob("[0-9]*.py")):
        return cwd_dir

    repo_dir = Path(__file__).resolve().parents[2] / "migrations"
    if any(repo_dir.glob("[0-9]*.py")):
        return repo_dir

    bundled_dir = Path(__file__).resolve().parent / "db_migrations"
    if any(bundled_dir.glob("[0-9]*.py")):
        return bundled_dir

    return cwd_dir


def sqlite_database_path(database_url: str) -> Path | None:
    """Return the filesystem path for a SQLite database URL."""
    if not database_url.startswith("sqlite:"):
        return None

    parsed = urlparse(database_url)
    if parsed.netloc and not parsed.path:
        return Path.cwd() / unquote(parsed.netloc)

    path = unquote(parsed.path or "")
    if database_url.startswith("sqlite:////"):
        return Path(path)
    if path.startswith("/"):
        return Path(path)
    return Path.cwd() / path


def prepare_sqlite_database(database_url: str) -> None:
    """Create parent directories so SQLite can create a new database file."""
    path = sqlite_database_path(database_url)
    if path is None:
        return
    if path.name:
        path.parent.mkdir(parents=True, exist_ok=True)


async def run_migrations(
    database: AsyncDatabase | None = None,
    *,
    migrations_dir: str | Path | None = None,
    db_alias: str = "default",
) -> list[str]:
    """Apply pending Oxyde migrations."""
    import ragtail.models  # noqa: F401

    _ = database
    directory = Path(migrations_dir) if migrations_dir is not None else resolve_migrations_dir()
    return await apply_migrations(migrations_dir=str(directory), db_alias=db_alias)


async def ensure_tables(database: AsyncDatabase | None = None) -> list[str]:
    """Apply database migrations (replaces legacy create_tables usage)."""
    _ = database
    return await run_migrations(database)


async def init_database(database_url: str) -> list[str]:
    """Prepare filesystem, connect, and apply migrations."""
    prepare_sqlite_database(database_url)
    await db.init(default=database_url)
    try:
        return await run_migrations()
    finally:
        await db.close()
