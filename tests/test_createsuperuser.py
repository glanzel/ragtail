import asyncio
from pathlib import Path

from oxyde import db

from ragtail.auth import verify_password
from ragtail.createsuperuser import main as createsuperuser_main
from ragtail.db import init_database
from ragtail.initdb import main as initdb_main
from ragtail.models import Locale, Page, User
from ragtail.routing import get_default_locale
from ragtail.seeddb import main as seeddb_main


async def _get_default_locale(database_url: str) -> Locale | None:
    await db.init(default=database_url)
    try:
        return await get_default_locale()
    finally:
        await db.close()


async def _count_root_pages(database_url: str, locale_id: int) -> int:
    await db.init(default=database_url)
    try:
        return await Page.objects.filter(locale_id=locale_id, depth=1).count()
    finally:
        await db.close()


async def _get_user(database_url: str, username: str) -> User | None:
    await db.init(default=database_url)
    try:
        return await User.objects.get_or_none(username=username)
    finally:
        await db.close()


def test_createsuperuser_creates_first_user(tmp_path: Path) -> None:
    database_url = f"sqlite:////{tmp_path / 'createsuperuser.db'}"
    asyncio.run(init_database(database_url))
    exit_code = createsuperuser_main(
        [
            "--database-url",
            database_url,
            "--username",
            "admin",
            "--email",
            "admin@example.com",
            "--password",
            "secret-pass",
            "--noinput",
        ]
    )
    assert exit_code == 0

    user = asyncio.run(_get_user(database_url, "admin"))
    assert user is not None
    assert user.is_staff is True
    assert user.email == "admin@example.com"
    assert verify_password("secret-pass", user.password_hash)


def test_createsuperuser_rejects_existing_user(tmp_path: Path) -> None:
    database_url = f"sqlite:////{tmp_path / 'createsuperuser-dup.db'}"
    asyncio.run(init_database(database_url))
    args = [
        "--database-url",
        database_url,
        "--username",
        "admin",
        "--email",
        "admin@example.com",
        "--password",
        "first-pass",
        "--noinput",
    ]
    assert createsuperuser_main(args) == 0
    assert createsuperuser_main(args) == 1


def test_createsuperuser_update_password(tmp_path: Path) -> None:
    database_url = f"sqlite:////{tmp_path / 'createsuperuser-update.db'}"
    asyncio.run(init_database(database_url))
    base_args = [
        "--database-url",
        database_url,
        "--username",
        "admin",
        "--email",
        "admin@example.com",
        "--noinput",
    ]
    assert createsuperuser_main([*base_args, "--password", "old-pass"]) == 0
    assert createsuperuser_main([*base_args, "--password", "new-pass", "--update"]) == 0

    user = asyncio.run(_get_user(database_url, "admin"))
    assert user is not None
    assert verify_password("new-pass", user.password_hash)


def test_initdb_creates_default_locale(tmp_path: Path) -> None:
    database_url = f"sqlite:////{tmp_path / 'initdb-locale.db'}"
    exit_code = initdb_main(
        [
            "--database-url",
            database_url,
            "--language-code",
            "de",
            "--display-name",
            "Deutsch",
            "--noinput",
        ]
    )
    assert exit_code == 0

    locale = asyncio.run(_get_default_locale(database_url))
    assert locale is not None
    assert locale.language_code == "de"
    assert locale.display_name == "Deutsch"
    assert locale.is_default is True
    assert asyncio.run(_count_root_pages(database_url, locale.id)) == 1


def test_initdb_skips_existing_default_locale(tmp_path: Path) -> None:
    database_url = f"sqlite:////{tmp_path / 'initdb-locale-skip.db'}"
    base_args = [
        "--database-url",
        database_url,
        "--language-code",
        "en",
        "--display-name",
        "English",
        "--noinput",
    ]
    assert initdb_main(base_args) == 0
    assert initdb_main([*base_args, "--language-code", "de", "--display-name", "Deutsch"]) == 0

    locale = asyncio.run(_get_default_locale(database_url))
    assert locale is not None
    assert locale.language_code == "en"


def test_seeddb_runs_initdb_and_createsuperuser(tmp_path: Path) -> None:
    database_url = f"sqlite:////{tmp_path / 'seeddb.db'}"
    exit_code = seeddb_main(
        [
            "--database-url",
            database_url,
            "--language-code",
            "de",
            "--display-name",
            "Deutsch",
            "--username",
            "admin",
            "--email",
            "admin@example.com",
            "--password",
            "secret-pass",
            "--noinput",
        ]
    )
    assert exit_code == 0

    locale = asyncio.run(_get_default_locale(database_url))
    assert locale is not None
    assert locale.language_code == "de"

    user = asyncio.run(_get_user(database_url, "admin"))
    assert user is not None
    assert user.is_staff is True
