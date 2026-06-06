# Oxytail

Oxytail is a very small Wagtail-inspired CMS MVP built on
[Oxyde ORM](https://oxyde.fatalyst.dev/). It intentionally starts with only the
core primitives:

- hierarchical `Page` model
- locale-aware pages for multilingual sites
- named navigation menus with nested menu items
- FastAPI routing for page delivery
- optional `oxyde-admin` registration for CRUD/admin screens

StreamField-like content blocks, images/documents, workflows and richer user
management are left for later iterations.

## Installation

```bash
pip install -e .
```

For the bundled admin integration:

```bash
pip install -e ".[admin]"
```

## Models

Oxytail provides Oxyde models in `oxytail.models`:

- `Locale`: active languages/locales, including the default locale
- `Page`: tree-structured page with `parent`, `path`, `depth`, `locale` and
  `translation_key`
- `Menu`: named menu per locale, for example `main` or `footer`
- `MenuItem`: nested menu entries pointing either to a `Page` or an external URL

Create an `oxyde_config.py` that points to the model module:

```python
DATABASES = {
    "default": "sqlite:///oxytail.db",
}

INSTALLED_MODELS = [
    "oxytail.models",
]
```

Then create and apply migrations:

```bash
oxyde makemigrations
oxyde migrate
```

## FastAPI app

```python
from oxytail.fastapi import create_app

app = create_app(database_url="sqlite:///oxytail.db")
```

This creates:

- `/api/cms/pages/{path}` for JSON page lookup
- `/api/cms/menus/{slug}` for JSON menu trees
- `/admin` when `oxytail[admin]` is installed
- a catch-all page route, which should be mounted last

By default pages are returned as JSON. Pass a renderer to serve templates or
another response format:

```python
from fastapi import Request
from fastapi.responses import HTMLResponse
from oxytail.fastapi import RouteMatch, create_app


async def render_page(request: Request, route: RouteMatch) -> HTMLResponse:
    return HTMLResponse(f"<h1>{route.page.title}</h1>{route.page.body or ''}")


app = create_app(database_url="sqlite:///oxytail.db", renderer=render_page)
```

## Routing and multilingual URLs

Oxytail stores page paths without a locale prefix, for example `/about/`. The
request resolver accepts locale-prefixed URLs such as `/de/ueber-uns/` and maps
them to the matching `Locale`.

```python
from oxytail.routing import join_page_path, localized_path, resolve_route

path = join_page_path("/", "about")  # "/about/"
public = localized_path(path, "de", default_language_code="en")  # "/de/about/"
route = await resolve_route("/de/about/")
```

Pages in different languages are linked by `translation_key`.

## Menus

Menus can be maintained through the admin or created with Oxyde directly. A menu
tree can be fetched as serializable nodes:

```python
from oxytail.menus import get_menu_tree

items = await get_menu_tree("main", language_code="en")
payload = [item.as_dict() for item in items]
```

## Admin

Oxytail does not implement a user system. For the MVP it delegates CRUD screens
to `oxyde-admin`:

```python
from fastapi import FastAPI
from oxyde import db
from oxytail.admin import create_fastapi_admin

app = FastAPI(lifespan=db.lifespan(default="sqlite:///oxytail.db"))
admin = create_fastapi_admin(title="CMS Admin")
app.mount("/admin", admin.app)
```
