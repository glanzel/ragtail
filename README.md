# Ragtail

Ragtail is a Wagtail-inspired CMS built on [Oxyde ORM](https://oxyde.fatalyst.dev/) and FastAPI. It ships with:

- hierarchical `Page` model
- locale-aware pages for multilingual sites
- named navigation menus with nested menu items
- FastAPI routing for page delivery (HTML via custom renderer, JSON API optional)
- **Wagtail-style admin** with login, page explorer, and page editor (PyJSX UI)
- optional legacy `oxyde-admin` CRUD integration

StreamField-like content blocks, images/documents, workflows and role-based permissions are left for later iterations.

## Installation

### As a library

```bash
uv add oxytail
```

Quick start — mount into an existing FastAPI app:

```python
from fastapi import FastAPI
from oxytail import FastAPICMS

cms = FastAPICMS(secret_key="change-me")
app = FastAPI(lifespan=cms.lifespan("sqlite://app.db"))
cms.mount(app)
```

Create the database, apply migrations, and add a staff user:

```bash
uv run oxytail-initdb --database-url sqlite://app.db
uv run oxytail-createsuperuser --username admin --email admin@example.com --password secret --noinput
```

Open http://localhost:8000/admin/ for the CMS admin.

More integration options (PyJSX, Jinja2, `create_app`): [docs/fastapi.md](docs/fastapi.md).

### Local development

```bash
make install
make migrate
make createsuperuser
make dev
```

Or in one step: `make setup`.

Details on migrations, environment variables, and frontend assets: [docs/installation.md](docs/installation.md).

## Documentation

| Topic | |
| --- | --- |
| [Installation](docs/installation.md) | Dependencies, migrations, admin user, env vars, Tailwind |
| [FastAPI integration](docs/fastapi.md) | `FastAPICMS`, `create_app`, renderers |
| [Models](docs/models.md) | `Page`, `Locale`, `Menu`, creating pages |
| [Admin](docs/admin.md) | Wagtail-style CMS UI, rich text |
| [Routing](docs/routing.md) | Multilingual URL resolution |
| [Menus](docs/menus.md) | Menu trees and API |
| [Demo](docs/demo.md) | Runnable example app and Docker |

## Demo

```bash
make dev
```

- Public site: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

See [docs/demo.md](docs/demo.md).
