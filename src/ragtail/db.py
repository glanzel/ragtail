from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

from oxyde import db
from oxyde.migrations import apply_migrations

from oxyde.db.pool import AsyncDatabase

_CONFIG_MISSING = (
    "No oxyde_config.py found in the current directory. "
    "Run 'oxyde init' to create configuration (skip if already initialized)."
)


def load_app_databases() -> dict[str, str]:
    """Return ``DATABASES`` from ``oxyde_config.py`` in the current working directory."""
    config_path = Path.cwd() / "oxyde_config.py"
    if not config_path.is_file():
        raise RuntimeError(_CONFIG_MISSING)

    sys.modules.pop("oxyde_config", None)
    spec = importlib.util.spec_from_file_location("oxyde_config", config_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(_CONFIG_MISSING)

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    databases = getattr(module, "DATABASES", None)
    if not databases:
        raise RuntimeError("No DATABASES configured in oxyde_config.py")
    return dict(databases)


def ragtail_migrations_dir() -> Path:
    """Bundled Ragtail migrations (``ragtail/migrations`` in the installed package)."""
    return Path(__file__).resolve().parent / "migrations"


def resolve_migrations_dir() -> Path:
    """Return the directory containing Ragtail's Oxyde migration files."""
    if configured := os.environ.get("RAGTAIL_MIGRATIONS_DIR"):
        return Path(configured)
    return ragtail_migrations_dir()


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
