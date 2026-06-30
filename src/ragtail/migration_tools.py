"""Generate and inspect Ragtail's bundled Oxyde migrations (package maintainers)."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import ragtail.images.models  # noqa: F401 — register image models
import ragtail.models  # noqa: F401 — register CMS models
from oxyde import db
from oxyde.core import migration_compute_diff
from oxyde.migrations import (
    extract_current_schema,
    generate_migration_file,
    get_applied_migrations,
    get_migration_files,
    replay_migrations,
)
from oxyde.migrations.utils import detect_dialect

from .db import load_app_databases, ragtail_migrations_dir


def _package_migrations_dir() -> Path:
    return ragtail_migrations_dir()


def _package_dialect() -> str:
    return detect_dialect("sqlite:///ragtail.db")


def makemigrations_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate Oxyde migration files for Ragtail's bundled models.",
    )
    parser.add_argument("--name", help="Migration name")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without writing a file",
    )
    args = parser.parse_args(argv)

    migrations_dir = _package_migrations_dir()
    dialect = _package_dialect()

    print("📝 Creating Ragtail package migrations...")
    print(f"   Directory: {migrations_dir}")
    print()

    print("1️⃣  Extracting schema from ragtail.models...")
    try:
        current_schema = extract_current_schema(dialect=dialect)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    table_count = len(current_schema["tables"])
    if table_count == 0:
        print("Error: no tables found in ragtail.models", file=sys.stderr)
        return 1
    print(f"   Found {table_count} table(s)")

    print()
    print("2️⃣  Replaying existing package migrations...")
    migrations_path = migrations_dir
    if not migrations_path.exists():
        old_schema = {"version": 1, "tables": {}}
    else:
        try:
            old_schema = replay_migrations(str(migrations_path))
        except Exception as exc:
            print(f"Error replaying migrations: {exc}", file=sys.stderr)
            return 1

    print()
    print("3️⃣  Computing diff...")
    try:
        operations_json = migration_compute_diff(
            json.dumps(old_schema),
            json.dumps(current_schema),
        )
        operations = json.loads(operations_json)
    except Exception as exc:
        print(f"Error computing diff: {exc}", file=sys.stderr)
        return 1

    if not operations:
        print("No changes detected.")
        return 0

    if args.dry_run:
        print(f"Would create migration with {len(operations)} operation(s).")
        return 0

    print()
    print("4️⃣  Writing migration file...")
    try:
        filepath = generate_migration_file(
            operations,
            migrations_dir=str(migrations_path),
            name=args.name,
        )
    except Exception as exc:
        print(f"Error generating migration: {exc}", file=sys.stderr)
        return 1

    print(f"Created: {filepath}")
    return 0


async def _applied_migration_names(database_url: str) -> set[str]:
    await db.init(default=database_url)
    try:
        return set(await get_applied_migrations("default"))
    finally:
        await db.close()


def showmigrations_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Show Ragtail package migrations and their apply status.",
    )
    parser.add_argument(
        "--database-url",
        help="Database URL to check applied migrations (default: oxyde_config.py)",
    )
    args = parser.parse_args(argv)

    migrations_dir = _package_migrations_dir()
    all_migrations = get_migration_files(str(migrations_dir))
    if not all_migrations:
        print(f"No migrations in {migrations_dir}")
        return 0

    applied_set: set[str] = set()
    if args.database_url:
        try:
            applied_set = asyncio.run(_applied_migration_names(args.database_url))
        except Exception as exc:
            print(f"Error reading database: {exc}", file=sys.stderr)
            return 1
    else:
        try:
            database_url = load_app_databases()["default"]
        except RuntimeError:
            print("📋 Package migrations:")
            for migration_path in all_migrations:
                print(f"  - {migration_path.stem}")
            print()
            print("Run from your app directory (with oxyde_config.py) or pass --database-url")
            return 0
        try:
            applied_set = asyncio.run(_applied_migration_names(database_url))
        except Exception as exc:
            print(f"Error reading database: {exc}", file=sys.stderr)
            return 1

    migration_names = [migration_path.stem for migration_path in all_migrations]
    applied_in_package = applied_set & set(migration_names)

    print("📋 Ragtail package migrations:")
    for name in migration_names:
        mark = "✓" if name in applied_set else " "
        print(f"  [{mark}] {name}")

    pending = len(migration_names) - len(applied_in_package)
    print()
    print(
        f"Total: {len(migration_names)}  "
        f"Applied: {len(applied_in_package)}  "
        f"Pending: {pending}"
    )
    return 0
