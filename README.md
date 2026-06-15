# Ragtail

Ragtail is a Ragtail CMS built on [Oxyde ORM](https://oxyde.fatalyst.dev/)
and FastAPI. It ships with:

- hierarchical `Page` model
- locale-aware pages for multilingual sites
- named navigation menus with nested menu items
- FastAPI routing for page delivery (HTML via custom renderer, JSON API optional)
- **Ragtail admin** with login, page explorer, and page editor (PyJSX UI)
- optional legacy `oxyde-admin` CRUD integration

StreamField-like content blocks, images/documents, workflows and role-based
permissions are left for later iterations.

## Installation

This project uses [uv](https://docs.astral.sh/uv/) for Python dependency management.

```bash
uv sync --locked
```

For the legacy oxyde-admin CRUD screens:

```bash
uv sync --locked --extra admin
```

For the demo application (includes uvicorn):

```bash
uv sync --locked --extra demo
```

Local development (demo + test dependencies):

```bash
make install
make createsuperuser   # first CMS staff user
make dev
# or: uv sync --locked --extra demo
```

### First admin user

Like Django's `createsuperuser`:

```bash
make createsuperuser
# non-interactive:
make createsuperuser USERNAME=admin EMAIL=admin@example.com PASSWORD=secret NOINPUT=1
# or:
uv run ragtail-createsuperuser --username admin --email admin@example.com --password secret --noinput
```

Environment variables:

- `RAGTAIL_DATABASE_URL` — database (default: `sqlite://ragtail.db`)
- `RAGTAIL_SUPERUSER_USERNAME` / `RAGTAIL_SUPERUSER_EMAIL` / `RAGTAIL_SUPERUSER_PASSWORD` — with `--noinput`

Use `--update` (or `make createsuperuser UPDATE=1`) to reset an existing user's password.

### Database migrations

Ragtail uses [Oxyde migrations](https://oxyde.fatalyst.dev/) (Django-style). Configuration lives in `oxyde_config.py`; migration files are in `migrations/`.

```bash
make migrate              # create DB file if needed, apply pending migrations
make makemigrations       # generate migration after model changes
make showmigrations       # list applied/pending migrations
```

Fresh database:

```bash
rm -f ragtail.db
make migrate
make createsuperuser
```

## Frontend (Tailwind CSS)

Admin and demo templates use [Tailwind CSS](https://tailwindcss.com/) utility
classes in PyJSX components. Compiled CSS is committed, but after changing
`.px` templates run:

```bash
npm install
npm run build:css
```

## Demo application

A runnable demo with Ragtail admin and PyJSX public templates lives in
`examples/demo/`:

```bash
uv run python examples/demo/main.py
# or: make dev
```

- Public site: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/
- Login: `admin` / `admin`

## Models

Ragtail provides Oxyde models in `ragtail.models`:

- `Locale`: active languages/locales, including the default locale
- `Page`: tree-structured page with `parent`, `path`, `depth`, `locale` and
  `translation_key`
- `Menu`: named menu per locale, for example `main` or `footer`
- `MenuItem`: nested menu entries pointing either to a `Page` or an external URL
- `User`: staff users for CMS admin login

Apply schema migrations:

```bash
make migrate
# after model changes:
make makemigrations MIGRATION_NAME=describe_change
make migrate
```

Programmatically:

```python
from oxyde import db
from ragtail.db import run_migrations

await db.init(default="sqlite://ragtail.db")
await run_migrations()
```

Create pages through the helper service so `path`, `depth` and
`translation_key` are filled consistently:

```python
from ragtail.pages import create_page, create_translation

home = await create_page(title="Home", slug="", locale=en, live=True)
about = await create_page(title="About", slug="about", parent=home, locale=en, live=True)
ueber_uns = await create_translation(about, title="Ueber uns", slug="ueber-uns", locale=de)
```

## Integration into an existing app

```python
from fastapi import FastAPI
from ragtail import FastAPICMS

cms = FastAPICMS(secret_key="change-me")
app = FastAPI(lifespan=cms.lifespan("sqlite://ragtail.db"))
cms.mount(app)
```

See [docs/integration.md](docs/integration.md).

## FastAPI app (greenfield)

```python
from ragtail.fastapi import create_app

app = create_app(
    database_url="sqlite://ragtail.db",
    mount_ragtail_admin=True,
    secret_key="replace-me",
)
```

This creates:

- `/admin/` Ragtail CMS admin (login required)
- `/api/cms/pages/{path}` for JSON page lookup
- `/api/cms/menus/{slug}` for JSON menu trees
- a catch-all page route, which should be mounted last

Pass a renderer to serve HTML templates (for example with PyJSX):

```python
from fastapi.responses import HTMLResponse
from ragtail.fastapi import create_app

app = create_app(
    database_url="sqlite://ragtail.db",
    renderer=my_html_renderer,
    mount_ragtail_admin=True,
)
```

See `examples/demo/` for a full PyJSX setup.

## Ragtail admin

Enable the built-in admin with session login:

```python
from ragtail.fastapi import create_app
from ragtail.auth import ensure_superuser

app = create_app(
    database_url="sqlite://ragtail.db",
    mount_ragtail_admin=True,
    secret_key="replace-me",
)

# once, e.g. in startup:
await ensure_superuser(username="admin", password="admin")
```

Features:

- Sign-in screen styled for Ragtail
- Sidebar navigation (Dashboard, Pages, Menus, Locales)
- Page explorer with tree + child listing
- Page editor (title, slug, SEO, publish settings)
- Locale management (add a second language, creates root page)
- Menu builder (create menus and add page/URL items)
- Create / edit / delete pages

### Demo rich text (TipTap)

The core `Page` model stores shared table columns. Declare type-specific fields on a
concrete page subclass; the admin picks them up automatically:

```python
from oxyde import Field
from ragtail import Page, register_page_model

@register_page_model
class ContentPage(Page):
    body: str | None = Field(default=None, db_type="TEXT")
```

See `examples/demo/pages.py` and `examples/demo/site_templates/content_page.px`.

The legacy generic `oxyde-admin` CRUD remains available via `mount_admin=True`.

## Routing and multilingual URLs

Ragtail stores page paths without a locale prefix, for example `/about/`. The
request resolver accepts locale-prefixed URLs such as `/de/ueber-uns/` and maps
them to the matching `Locale`.

```python
from ragtail.routing import join_page_path, localized_path, resolve_route

path = join_page_path("/", "about")  # "/about/"
public = localized_path(path, "de", default_language_code="en")  # "/de/about/"
route = await resolve_route("/de/about/")
```

Pages in different languages are linked by `translation_key`.

## Menus

Menus can be maintained through the admin or created with Oxyde directly. A menu
tree can be fetched as serializable nodes:

```python
from ragtail.menus import create_menu, create_menu_item, get_menu_tree

main = await create_menu(name="Main", slug="main", locale=en)
await create_menu_item(menu=main, label="About", page=about)

items = await get_menu_tree("main", language_code="en")
payload = [item.as_dict() for item in items]
```
