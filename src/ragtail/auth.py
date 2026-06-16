from __future__ import annotations

import re

import bcrypt

from .models import User

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


async def authenticate_user(username: str, password: str) -> User | None:
    user = await User.objects.get_or_none(username=username, is_active=True, is_staff=True)
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


def normalize_email(email: str) -> str:
    return email.strip().lower()


def email_error(email: str) -> str | None:
    normalized = normalize_email(email)
    if not normalized:
        return "Email address is required."
    if not _EMAIL_RE.match(normalized):
        return "Enter a valid email address."
    return None


async def create_user(
    *,
    username: str,
    email: str,
    password: str,
    is_active: bool = True,
    is_staff: bool = True,
) -> User:
    return await User.objects.create(
        username=username,
        email=normalize_email(email),
        password_hash=hash_password(password),
        is_active=is_active,
        is_staff=is_staff,
    )


async def update_user(
    user: User,
    *,
    email: str | None = None,
    password: str | None = None,
    is_active: bool | None = None,
    is_staff: bool | None = None,
) -> User:
    if email is not None:
        user.email = normalize_email(email)
    if password:
        user.password_hash = hash_password(password)
    if is_active is not None:
        user.is_active = is_active
    if is_staff is not None:
        user.is_staff = is_staff
    await user.save()
    return user


async def reset_user_password(user: User, *, password: str) -> User:
    return await update_user(user, password=password)


def change_password_error(
    user: User,
    *,
    current_password: str,
    new_password: str,
    confirm_password: str,
) -> str | None:
    if not current_password or not new_password:
        return "Current password and new password are required."
    if new_password != confirm_password:
        return "New passwords do not match."
    if not verify_password(current_password, user.password_hash):
        return "Current password is incorrect."
    return None


def reset_password_error(*, password: str, confirm_password: str) -> str | None:
    if not password:
        return "Password is required."
    if password != confirm_password:
        return "Passwords do not match."
    return None


async def ensure_superuser(
    *,
    username: str,
    password: str,
    email: str | None = None,
) -> User:
    existing = await User.objects.get_or_none(username=username)
    if existing is not None:
        return existing
    return await create_user(
        username=username,
        email=email or f"{username}@localhost",
        password=password,
        is_staff=True,
    )
