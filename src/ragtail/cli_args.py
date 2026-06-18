from __future__ import annotations

import argparse


def add_locale_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--language-code",
        help="Default locale language code (for example en or de)",
    )
    parser.add_argument(
        "--display-name",
        help="Default locale display name (for example English or Deutsch)",
    )


def add_superuser_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--username", help="Staff username")
    parser.add_argument("--email", help="Staff email address")
    parser.add_argument("--password", help="Staff password (avoid on shared shells)")
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update password when the username already exists",
    )


def add_noinput_argument(parser: argparse.ArgumentParser, *, help_text: str) -> None:
    parser.add_argument(
        "--noinput",
        action="store_true",
        help=help_text,
    )
