from __future__ import annotations

from fastapi import Request

from ..models import User

SESSION_USER_KEY = "ragtail_user_id"


class AdminLoginRequired(Exception):
    def __init__(self, next_url: str) -> None:
        self.next_url = next_url


async def get_optional_user(request: Request) -> User | None:
    user_id = request.session.get(SESSION_USER_KEY)
    if not user_id:
        return None
    return await User.objects.get_or_none(id=user_id, is_active=True, is_staff=True)


async def require_user(request: Request) -> User:
    user = await get_optional_user(request)
    if user is None:
        raise AdminLoginRequired(str(request.url.path))
    return user
