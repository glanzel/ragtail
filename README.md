# Oxytail

Oxytail is a Wagtail-inspired CMS built on [Oxyde ORM](https://oxyde.fatalyst.dev/)
and FastAPI. It ships with:

- hierarchical `Page` model
- locale-aware pages for multilingual sites
- named navigation menus with nested menu items
- FastAPI routing for page delivery (HTML via custom renderer, JSON API optional)
- **Wagtail-style admin** with login, page explorer, and page editor (PyJSX UI)
- optional legacy `oxyde-admin` CRUD integration

StreamField-like content blocks, images/documents, workflows and role-based
permissions are left for later iterations.

## Installation

```bash
pip install -e .
```

For the legacy oxyde-admin CRUD screens:

```bash
pip install -e ".[admin]"
```

For the demo application:

```bash
pip install -e ".[demo]"
```

## Demo application

A runnable demo with Wagtail-style admin and PyJSX public templates lives in
`examples/demo/`:

```bash
python examples/demo/main.py
```

- Public site: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/
- Login: `admin` / `admin`

## Models

Oxytail provides Oxyde models in `oxytail.models`:

- `Locale`: active languages/locales, including the default locale
- `Page`: tree-structured page with `parent`, `path`, `depth`, `locale` and
  `translation_key`
- `Menu`: named menu per locale, for example `main` or `footer`
- `MenuItem`: nested menu entries pointing either to a `Page` or an external URL
- `User`: staff users for CMS admin login

Create tables with Oxyde:

```python
from oxyde import create_tables, db

database = await db.get_connection("default")
await create_tables(database)
```

Create pages through the helper service so `path`, `depth` and
`translation_key` are filled consistently:

```python
from oxytail.pages import create_page, create_translation

home = await create_page(title="Home", slug="", locale=en, live=True)
about = await create_page(title="About", slug="about", parent=home, locale=en, live=True)
ueber_uns = await create_translation(about, title="Ueber uns", slug="ueber-uns", locale=de)
```

## FastAPI app

```python
from oxytail.fastapi import create_app

app = create_app(
    database_url="sqlite:///oxytail.db",
    mount_wagtail_admin=True,
    secret_key="replace-me",
)
```

This creates:

- `/admin/` Wagtail-style CMS admin (login required)
- `/api/cms/pages/{path}` for JSON page lookup
- `/api/cms/menus/{slug}` for JSON menu trees
- a catch-all page route, which should be mounted last

Pass a renderer to serve HTML templates (for example with PyJSX):

```python
from fastapi.responses import HTMLResponse
from oxytail.fastapi import create_app

app = create_app(
    database_url="sqlite:///oxytail.db",
    renderer=my_html_renderer,
    mount_wagtail_admin=True,
)
```

See `examples/demo/` for a full PyJSX setup.

## Wagtail-style admin

Enable the built-in admin with session login:

```python
from oxytail.fastapi import create_app
from oxytail.auth import ensure_superuser

app = create_app(
    database_url="sqlite:///oxytail.db",
    mount_wagtail_admin=True,
    secret_key="replace-me",
)

# once, e.g. in startup:
await ensure_superuser(username="admin", password="admin")
```

Features:

- Sign-in screen styled like Wagtail
- Sidebar navigation (Dashboard, Pages)
- Page explorer with tree + child listing
- Page editor (Content, Promote, Settings panels)
- Create / edit / delete pages

The legacy generic `oxyde-admin` CRUD remains available via `mount_admin=True`.

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
from oxytail.menus import create_menu, create_menu_item, get_menu_tree

main = await create_menu(name="Main", slug="main", locale=en)
await create_menu_item(menu=main, label="About", page=about)

items = await get_menu_tree("main", language_code="en")
payload = [item.as_dict() for item in items]
```
