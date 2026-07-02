# Routing and multilingual URLs

Ragtail uses one **Site** per domain. The site's `root_page` defines the default language and is served at `/`. Translated homepages are served at locale prefixes such as `/de/`.

Page paths are stored without a locale prefix, for example `/about/`. The site homepage is always served at `/`; its slug (for example `home`) does not appear in descendant URLs, so a child page `about` is `/about/`, not `/home/about/`. The request resolver accepts locale-prefixed URLs such as `/de/ueber/` and maps them to the matching `Locale`.

```python
from ragtail.routing import join_page_path, localized_path, resolve_route

path = join_page_path("/", "about")  # "/about/"
public = localized_path(path, "de", default_language_code="en")  # "/de/about/"
route = await resolve_route("/de/about/")
```

Pages in different languages are linked by `translation_key`.

## Site configuration

- **root_page**: homepage in the default language (served at `/`)
- **prefix_default_language**: when enabled, the default language also uses a URL prefix (for example `/en/` instead of `/`)

Other locales resolve their homepage by finding the translation of `root_page`.

## Language switcher

Use `get_translation_alternates(page)` to build links to translated siblings:

```python
from ragtail.routing import get_translation_alternates

alternates = await get_translation_alternates(page, current_locale=route.locale)
# [{"language_code": "de", "display_name": "Deutsch", "url": "/de/ueber/", "is_current": False}, ...]
```

Alternates are also available in template context as `translation_alternates` and in the JSON API as `alternates`.
