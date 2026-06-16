import asyncio
from pathlib import Path

from oxyde import db

from ragtail.auth import verify_password
from ragtail.createsuperuser import main
from ragtail.models import User


async def _get_user(database_url: str, username: str) -> User | None:
    await db.init(default=database_url)
    try:
        return await User.objects.get_or_none(username=username)
    finally:
        await db.close()


def test_createsuperuser_creates_first_user(tmp_path: Path) -> None:
    database_url = f"sqlite:////{tmp_path / 'createsuperuser.db'}"
    exit_code = main(
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
    assert main(args) == 0
    assert main(args) == 1


def test_createsuperuser_update_password(tmp_path: Path) -> None:
    database_url = f"sqlite:////{tmp_path / 'createsuperuser-update.db'}"
    base_args = [
        "--database-url",
        database_url,
        "--username",
        "admin",
        "--email",
        "admin@example.com",
        "--noinput",
    ]
    assert main([*base_args, "--password", "old-pass"]) == 0
    assert main([*base_args, "--password", "new-pass", "--update"]) == 0

    user = asyncio.run(_get_user(database_url, "admin"))
    assert user is not None
    assert verify_password("new-pass", user.password_hash)
