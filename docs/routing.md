# Routing and multilingual URLs

Ragtail stores page paths without a locale prefix, for example `/about/`. The request resolver accepts locale-prefixed URLs such as `/de/ueber-uns/` and maps them to the matching `Locale`.

```python
from oxytail.routing import join_page_path, localized_path, resolve_route

path = join_page_path("/", "about")  # "/about/"
public = localized_path(path, "de", default_language_code="en")  # "/de/about/"
route = await resolve_route("/de/about/")
```

Pages in different languages are linked by `translation_key`.
