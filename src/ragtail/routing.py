from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from .models import Locale, Page


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


@dataclass(frozen=True)
class TranslationAlternate:
    language_code: str
    display_name: str
    url: str
    is_current: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "language_code": self.language_code,
            "display_name": self.display_name,
            "url": self.url,
            "is_current": self.is_current,
        }


async def get_default_locale() -> Locale | None:
    from .sites import get_default_site, get_site_default_locale

    site = await get_default_site()
    if site is not None:
        site_locale = await get_site_default_locale(site)
        if site_locale is not None:
            return site_locale
    return await Locale.objects.filter(is_default=True, is_active=True).order_by("sort_order").first()


async def get_active_locales() -> list[Locale]:
    return await Locale.objects.filter(is_active=True).order_by("sort_order", "language_code").all()


async def get_locale(language_code: str | None = None) -> Locale | None:
    if language_code:
        return await Locale.objects.get_or_none(language_code=language_code, is_active=True)
    return await get_default_locale()


async def get_site_routing_settings() -> tuple[Locale | None, bool]:
    from .sites import get_default_site

    default_locale = await get_default_locale()
    site = await get_default_site()
    if site is not None:
        return default_locale, site.prefix_default_language
    return default_locale, False


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
    from .sites import get_default_site, get_homepage_for_locale, is_tree_root

    site = await get_default_site()
    if site is None:
        return None

    page = await get_homepage_for_locale(site, locale)
    if page is None or is_tree_root(page):
        return None
    if not include_unpublished and not page.live:
        return None
    return page


async def _resolve_page_under_homepage(
    local_path: str,
    locale: Locale,
    homepage: Page,
    *,
    include_unpublished: bool,
) -> Page | None:
    from .sites import TREE_ROOT_CONTENT_TYPE, is_page_publicly_routable, is_tree_root

    normalized = normalize_path(local_path)
    if normalized == "/":
        if is_tree_root(homepage):
            return None
        if not include_unpublished and not homepage.live:
            return None
        return homepage

    slugs = [part for part in normalized.strip("/").split("/") if part]
    current = homepage
    for slug in slugs:
        child = await Page.objects.filter(
            parent_id=current.id,
            slug=slug,
            locale_id=locale.id,
        ).exclude(content_type=TREE_ROOT_CONTENT_TYPE).first()
        if child is None:
            return None
        current = child

    if not include_unpublished and not current.live:
        return None
    if not await is_page_publicly_routable(current, locale):
        return None
    return current


async def build_public_path_from_homepage(page: Page, homepage: Page) -> str:
    """Build the public URL path for a page relative to the site homepage."""

    if page.id == homepage.id:
        return "/"

    segments: list[str] = []
    current_id = page.id
    while current_id is not None and current_id != homepage.id:
        current = await Page.objects.get_or_none(id=current_id)
        if current is None:
            return normalize_path(page.path)
        if current.slug:
            segments.append(current.slug.strip("/"))
        current_id = current.parent_id

    segments.reverse()
    if not segments:
        return "/"
    return normalize_path("/".join(segments))


async def _resolve_public_page(
    local_path: str,
    locale: Locale,
    *,
    include_unpublished: bool,
) -> Page | None:
    from .sites import TREE_ROOT_CONTENT_TYPE, get_default_site, get_homepage_for_locale, is_page_publicly_routable

    normalized = normalize_path(local_path)
    if normalized == "/":
        return await _resolve_site_root_page(locale, include_unpublished=include_unpublished)

    page = await Page.objects.filter(
        path=normalized,
        locale_id=locale.id,
    ).exclude(content_type=TREE_ROOT_CONTENT_TYPE).first()
    if page is not None:
        if not include_unpublished and not page.live:
            return None
        if not await is_page_publicly_routable(page, locale):
            return None
        return page

    site = await get_default_site()
    homepage = await get_homepage_for_locale(site, locale) if site is not None else None
    if homepage is None:
        return None
    return await _resolve_page_under_homepage(
        normalized,
        locale,
        homepage,
        include_unpublished=include_unpublished,
    )


async def _localized_public_path_for_page(
    page: Page,
    locale: Locale,
    *,
    local_path: str | None = None,
) -> str:
    from .sites import get_default_site, get_homepage_for_locale

    default_locale, prefix_default_language = await get_site_routing_settings()
    default_language_code = default_locale.language_code if default_locale else None
    site = await get_default_site()
    homepage = await get_homepage_for_locale(site, locale) if site is not None else None
    if homepage is not None:
        page_path = await build_public_path_from_homepage(page, homepage)
    elif local_path is not None and normalize_path(local_path) == "/":
        page_path = "/"
    else:
        page_path = page.path

    return localized_path(
        page_path,
        locale.language_code,
        default_language_code=default_language_code,
        prefix_default_language=prefix_default_language,
    )


async def resolve_route(
    path: str,
    *,
    language_code: str | None = None,
    include_unpublished: bool = False,
) -> RouteMatch | None:
    """Resolve an incoming URL, including optional locale prefixes."""

    locales = await get_active_locales()
    if not locales:
        return None

    default_locale, _prefix_default_language = await get_site_routing_settings()
    if default_locale is None:
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
        public_path = await _localized_public_path_for_page(
            page,
            locale,
            local_path=local_path,
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
        public_path=await _localized_public_path_for_page(
            default_page,
            locale,
            local_path=local_path,
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


async def get_translation_alternates(
    page: Page,
    *,
    current_locale: Locale | None = None,
) -> list[TranslationAlternate]:
    """Return public URLs for translated siblings of a page."""

    if page.translation_key is None:
        return []

    page_locale = current_locale
    if page_locale is None and page.locale_id is not None:
        page_locale = page.locale
        if page_locale is None:
            page_locale = await Locale.objects.get_or_none(id=page.locale_id)

    alternates: list[TranslationAlternate] = []
    for locale in await get_active_locales():
        if locale.id == page.locale_id:
            translation = page
        else:
            translation = await get_translation(page, locale.language_code)
        if translation is None:
            continue
        public_url = await get_page_public_url(translation)
        if public_url is None:
            continue
        alternates.append(
            TranslationAlternate(
                language_code=locale.language_code,
                display_name=locale.display_name,
                url=public_url,
                is_current=page_locale is not None and locale.id == page_locale.id,
            )
        )
    return alternates


async def get_page_public_url(page: Page) -> str | None:
    """Return the public URL path for a page, or None if it is not in the site tree."""

    from .sites import get_default_site, get_homepage_for_locale, is_page_publicly_routable, is_tree_root

    if is_tree_root(page) or page.locale_id is None:
        return None

    locale = page.locale
    if locale is None:
        locale = await Locale.objects.get_or_none(id=page.locale_id)
    if locale is None:
        return None
    if not await is_page_publicly_routable(page, locale):
        return None

    default_locale, prefix_default_language = await get_site_routing_settings()
    default_language_code = default_locale.language_code if default_locale else None
    site = await get_default_site()
    homepage = await get_homepage_for_locale(site, locale) if site is not None else None
    if homepage is not None:
        page_path = await build_public_path_from_homepage(page, homepage)
    else:
        page_path = page.path

    return localized_path(
        page_path,
        locale.language_code,
        default_language_code=default_language_code,
        prefix_default_language=prefix_default_language,
    )
