from __future__ import annotations

import argparse
import asyncio
import os
import sys

from .db import init_database


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create the database (if needed) and apply Ragtail migrations.",
    )
    parser.add_argument(
        "--database-url",
        default=os.environ.get("RAGTAIL_DATABASE_URL", "sqlite://ragtail.db"),
        help="Database URL (default: RAGTAIL_DATABASE_URL or sqlite://ragtail.db)",
    )
    return parser


async def _run(args: argparse.Namespace) -> int:
    applied = await init_database(args.database_url)
    if applied:
        print(f"Applied {len(applied)} migration(s).")
    else:
        print("Database schema is up to date.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        return asyncio.run(_run(args))
    except Exception as exc:  # pragma: no cover - surfaced to CLI
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
