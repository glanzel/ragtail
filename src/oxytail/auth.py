from __future__ import annotations

import bcrypt

from .models import User


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


async def authenticate_user(username: str, password: str) -> User | None:
    user = await User.objects.get_or_none(username=username, is_active=True, is_staff=True)
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


async def create_user(*, username: str, password: str, is_staff: bool = True) -> User:
    return await User.objects.create(
        username=username,
        password_hash=hash_password(password),
        is_active=True,
        is_staff=is_staff,
    )


async def ensure_superuser(*, username: str, password: str) -> User:
    existing = await User.objects.get_or_none(username=username)
    if existing is not None:
        return existing
    return await create_user(username=username, password=password, is_staff=True)
