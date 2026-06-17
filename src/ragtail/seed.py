from __future__ import annotations

import os

from .models import Locale
from .ragtail_admin.services import _clear_other_default_locales, create_locale, ensure_root_page
from .routing import get_default_locale

DEFAULT_LANGUAGE_CODE = "en"
DEFAULT_DISPLAY_NAME = "English"


def default_language_code() -> str:
    return os.environ.get("RAGTAIL_DEFAULT_LOCALE_CODE", DEFAULT_LANGUAGE_CODE).strip().lower()


def default_display_name(language_code: str) -> str:
    configured = os.environ.get("RAGTAIL_DEFAULT_LOCALE_NAME", "").strip()
    if configured:
        return configured
    known = {"en": "English", "de": "Deutsch"}
    return known.get(language_code, language_code)


def prompt_language_code() -> str:
    while True:
        code = input(f"Language code [{DEFAULT_LANGUAGE_CODE}]: ").strip().lower()
        if not code:
            return DEFAULT_LANGUAGE_CODE
        return code


def prompt_display_name(language_code: str) -> str:
    suggested = default_display_name(language_code)
    name = input(f"Display name [{suggested}]: ").strip()
    return name or suggested


def resolve_locale_credentials(
    *,
    language_code: str | None,
    display_name: str | None,
    noinput: bool,
) -> tuple[str, str]:
    code = (language_code or "").strip().lower()
    name = (display_name or "").strip()

    if noinput:
        resolved_code = code or default_language_code()
        resolved_name = name or default_display_name(resolved_code)
        return resolved_code, resolved_name

    if not code:
        code = prompt_language_code()
    if not name:
        name = prompt_display_name(code)
    return code, name


async def ensure_default_locale(
    *,
    language_code: str,
    display_name: str,
) -> tuple[Locale, bool]:
    """Ensure an active default locale exists. Returns ``(locale, created)``."""

    existing_default = await get_default_locale()
    if existing_default is not None:
        await ensure_root_page(existing_default)
        return existing_default, False

    code = language_code.strip().lower()
    name = display_name.strip()
    if not code or not name:
        raise ValueError("Language code and display name are required.")

    existing = await Locale.objects.get_or_none(language_code=code)
    if existing is not None:
        if not existing.is_default:
            await _clear_other_default_locales(exclude_locale_id=existing.id)
            existing.is_default = True
            existing.is_active = True
            if name:
                existing.display_name = name
            await existing.save()
        await ensure_root_page(existing)
        return existing, False

    locale = await create_locale(
        language_code=code,
        display_name=name,
        is_default=True,
    )
    await ensure_root_page(locale)
    return locale, True
