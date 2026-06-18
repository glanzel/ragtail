from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from .models import Locale, Page, Site


def normalize_path(path: str | None) -> str:
    """Return a canonical CMS path with leading and trailing slashes."""

    if not path:
        return "/"

    normalized = "/" + path.strip("/")
    if normalized == "/":
        return normalized
    return f"{normalized}/"


def join_page_path(parent_path: str | None, slug: str | None) -> str:
    """Build a child page path from a parent path and slug."""

    clean_slug = (slug or "").strip("/")
    if not clean_slug:
        return normalize_path(parent_path)
    return normalize_path(f"{normalize_path(parent_path).rstrip('/')}/{clean_slug}")


def strip_locale_prefix(path: str, language_codes: Iterable[str]) -> tuple[str | None, str]:
    """Split `/de/about/` into `("de", "/about/")` when the prefix is a locale."""

    normalized = normalize_path(path)
    if normalized == "/":
        return None, normalized

    parts = normalized.strip("/").split("/", 1)
    prefix = parts[0]
    if prefix not in set(language_codes):
        return None, normalized

    remaining = parts[1] if len(parts) > 1 else ""
    return prefix, normalize_path(remaining)


def localized_path(
    page_path: str,
    language_code: str,
    *,
    default_language_code: str | None = None,
    prefix_default_language: bool = False,
) -> str:
    """Return the public URL for a page path and locale."""

    normalized = normalize_path(page_path)
    if language_code == default_language_code and not prefix_default_language:
        return normalized
    return normalize_path(f"/{language_code}/{normalized.strip('/')}")


@dataclass(frozen=True)
class RouteMatch:
    """Result of resolving an incoming request path."""

    page: Page
    locale: Locale
    path: str
    public_path: str
    is_fallback: bool = False


async def get_default_locale() -> Locale | None:
    return await Locale.objects.filter(is_default=True, is_active=True).order_by("sort_order").first()


async def get_active_locales() -> list[Locale]:
    return await Locale.objects.filter(is_active=True).order_by("sort_order", "language_code").all()


async def get_locale(language_code: str | None = None) -> Locale | None:
    if language_code:
        return await Locale.objects.get_or_none(language_code=language_code, is_active=True)
    return await get_default_locale()


async def get_site_for_locale(locale: Locale) -> Site | None:
    return await Site.objects.filter(locale_id=locale.id).first()


async def resolve_page(
    path: str,
    *,
    language_code: str | None = None,
    include_unpublished: bool = False,
) -> Page | None:
    """Resolve a canonical page path for one locale."""

    route = await resolve_route(
        path,
        language_code=language_code,
        include_unpublished=include_unpublished,
    )
    return route.page if route is not None else None


async def _resolve_site_root_page(
    locale: Locale,
    *,
    include_unpublished: bool,
) -> Page | None:
    from .sites import is_tree_root

    site = await get_site_for_locale(locale)
    if site is None or site.root_page_id is None:
        return None
    page = await Page.objects.get_or_none(id=site.root_page_id, locale_id=locale.id)
    if page is None or is_tree_root(page):
        return None
    if not include_unpublished and not page.live:
        return None
    return page


async def _resolve_public_page(
    local_path: str,
    locale: Locale,
    *,
    include_unpublished: bool,
) -> Page | None:
    from .sites import TREE_ROOT_CONTENT_TYPE, is_page_publicly_routable

    normalized = normalize_path(local_path)
    if normalized == "/":
        return await _resolve_site_root_page(locale, include_unpublished=include_unpublished)

    page = await Page.objects.filter(
        path=normalized,
        locale_id=locale.id,
    ).exclude(content_type=TREE_ROOT_CONTENT_TYPE).first()
    if page is None:
        return None
    if not include_unpublished and not page.live:
        return None
    if not await is_page_publicly_routable(page, locale):
        return None
    return page


async def resolve_route(
    path: str,
    *,
    language_code: str | None = None,
    include_unpublished: bool = False,
    prefix_default_language: bool = False,
) -> RouteMatch | None:
    """Resolve an incoming URL, including optional locale prefixes."""

    locales = await get_active_locales()
    if not locales:
        return None

    default_locale = next((locale for locale in locales if locale.is_default), locales[0])
    language_codes = [locale.language_code for locale in locales]
    prefix_language, local_path = strip_locale_prefix(path, language_codes)

    requested_language = language_code or prefix_language or default_locale.language_code
    locale = next((locale for locale in locales if locale.language_code == requested_language), None)
    if locale is None:
        return None

    page = await _resolve_public_page(
        local_path,
        locale,
        include_unpublished=include_unpublished,
    )
    if page is not None:
        public_path = localized_path(
            "/" if local_path == "/" else page.path,
            locale.language_code,
            default_language_code=default_locale.language_code,
            prefix_default_language=prefix_default_language,
        )
        return RouteMatch(
            page=page,
            locale=locale,
            path=normalize_path(local_path),
            public_path=public_path,
        )

    if locale.id == default_locale.id:
        return None

    default_page = await _resolve_public_page(
        local_path,
        default_locale,
        include_unpublished=include_unpublished,
    )
    if default_page is None:
        return None

    if not include_unpublished and not default_page.live:
        return None

    return RouteMatch(
        page=default_page,
        locale=locale,
        path=normalize_path(local_path),
        public_path=localized_path(
            "/" if local_path == "/" else default_page.path,
            locale.language_code,
            default_language_code=default_locale.language_code,
            prefix_default_language=prefix_default_language,
        ),
        is_fallback=True,
    )


async def get_translation(page: Page, language_code: str) -> Page | None:
    """Find the translated sibling for a page using its translation key."""

    if page.translation_key is None:
        return None

    locale = await get_locale(language_code)
    if locale is None:
        return None
    return await Page.objects.filter(translation_key=page.translation_key, locale_id=locale.id).first()
