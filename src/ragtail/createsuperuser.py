from __future__ import annotations

import argparse
import asyncio
import getpass
import os
import sys

from oxyde import db

from .auth import create_user, email_error, normalize_email, update_user
from .db import init_database
from .models import User


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a Ragtail CMS staff user (like Django's createsuperuser).",
    )
    parser.add_argument(
        "--database-url",
        default=os.environ.get("RAGTAIL_DATABASE_URL", "sqlite://ragtail.db"),
        help="Database URL (default: RAGTAIL_DATABASE_URL or sqlite://ragtail.db)",
    )
    parser.add_argument("--username", help="Staff username")
    parser.add_argument("--email", help="Staff email address")
    parser.add_argument("--password", help="Staff password (avoid on shared shells)")
    parser.add_argument(
        "--noinput",
        action="store_true",
        help="Non-interactive mode (requires --username, --email and --password)",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update password when the username already exists",
    )
    return parser


def _prompt_username() -> str:
    while True:
        username = input("Username: ").strip()
        if username:
            return username
        print("Error: username is required.")


def _prompt_email() -> str:
    while True:
        email = input("Email address: ").strip()
        error = email_error(email)
        if error:
            print(f"Error: {error}")
            continue
        return email


def _prompt_password() -> str:
    while True:
        password = getpass.getpass("Password: ")
        if not password:
            print("Error: password is required.")
            continue
        confirm = getpass.getpass("Password (again): ")
        if password != confirm:
            print("Error: passwords do not match.")
            continue
        return password


def _resolve_credentials(args: argparse.Namespace) -> tuple[str, str, str]:
    username = (args.username or os.environ.get("RAGTAIL_SUPERUSER_USERNAME", "")).strip()
    email = (args.email or os.environ.get("RAGTAIL_SUPERUSER_EMAIL", "")).strip()
    password = args.password or os.environ.get("RAGTAIL_SUPERUSER_PASSWORD", "")

    if args.noinput:
        if not username or not email or not password:
            raise SystemExit(
                "Non-interactive mode requires --username, --email and --password "
                "(or RAGTAIL_SUPERUSER_USERNAME, RAGTAIL_SUPERUSER_EMAIL and "
                "RAGTAIL_SUPERUSER_PASSWORD)."
            )
        validation_error = email_error(email)
        if validation_error:
            raise SystemExit(validation_error)
        return username, email, password

    if not username:
        username = _prompt_username()
    if not email:
        email = _prompt_email()
    if not password:
        password = _prompt_password()
    validation_error = email_error(email)
    if validation_error:
        raise SystemExit(validation_error)
    return username, email, password


async def _run(args: argparse.Namespace) -> int:
    username, email, password = _resolve_credentials(args)
    normalized_email = normalize_email(email)

    await init_database(args.database_url)
    await db.init(default=args.database_url)
    try:
        existing = await User.objects.get_or_none(username=username)
        if existing is not None:
            if not args.update:
                print(f"Error: user '{username}' already exists.", file=sys.stderr)
                return 1
            await update_user(
                existing,
                email=normalized_email,
                password=password,
                is_active=True,
                is_staff=True,
            )
            print(f"Updated staff user '{username}'.")
            return 0

        email_taken = await User.objects.get_or_none(email=normalized_email)
        if email_taken is not None:
            print(f"Error: email '{normalized_email}' is already in use.", file=sys.stderr)
            return 1

        await create_user(
            username=username,
            email=normalized_email,
            password=password,
            is_active=True,
            is_staff=True,
        )
        print(f"Created staff user '{username}'.")
        return 0
    finally:
        await db.close()


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return asyncio.run(_run(args))


if __name__ == "__main__":
    raise SystemExit(main())
