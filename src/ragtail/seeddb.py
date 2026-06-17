from __future__ import annotations

import argparse
import asyncio
import sys

from . import createsuperuser, initdb
from .cli_args import (
    add_database_argument,
    add_locale_arguments,
    add_noinput_argument,
    add_superuser_arguments,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Initialize the Ragtail database (migrations + default locale) "
            "and create a staff user."
        ),
    )
    add_database_argument(parser)
    add_locale_arguments(parser)
    add_superuser_arguments(parser)
    add_noinput_argument(
        parser,
        help_text=(
            "Non-interactive mode (uses locale defaults or RAGTAIL_DEFAULT_LOCALE_*; "
            "requires superuser credentials or RAGTAIL_SUPERUSER_*)"
        ),
    )
    return parser


async def run(args: argparse.Namespace) -> int:
    init_exit = await initdb.run(args)
    if init_exit != 0:
        return init_exit
    return await createsuperuser.run(args)


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        return asyncio.run(run(args))
    except SystemExit as exc:
        raise exc
    except Exception as exc:  # pragma: no cover - surfaced to CLI
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
