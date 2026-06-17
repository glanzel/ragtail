from __future__ import annotations

import argparse
import asyncio
import sys

from oxyde import db

from .cli_args import add_database_argument, add_locale_arguments, add_noinput_argument
from .db import init_database
from .seed import resolve_locale_credentials
from .seed import ensure_default_locale as seed_default_locale


def add_arguments(parser: argparse.ArgumentParser) -> None:
    add_database_argument(parser)
    add_locale_arguments(parser)
    add_noinput_argument(
        parser,
        help_text="Non-interactive mode (uses defaults or RAGTAIL_DEFAULT_LOCALE_* env vars)",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create the database (if needed), apply Ragtail migrations, and seed a default locale.",
    )
    add_arguments(parser)
    return parser


async def run(args: argparse.Namespace) -> int:
    applied = await init_database(args.database_url)
    if applied:
        print(f"Applied {len(applied)} migration(s).")
    else:
        print("Database schema is up to date.")

    language_code, display_name = resolve_locale_credentials(
        language_code=args.language_code,
        display_name=args.display_name,
        noinput=args.noinput,
    )

    await db.init(default=args.database_url)
    try:
        locale, created = await seed_default_locale(
            language_code=language_code,
            display_name=display_name,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        await db.close()

    if created:
        print(f"Created default locale {locale.language_code} ({locale.display_name}).")
    else:
        print(
            f"Default locale already configured ({locale.language_code}: {locale.display_name})."
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        return asyncio.run(run(args))
    except Exception as exc:  # pragma: no cover - surfaced to CLI
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
