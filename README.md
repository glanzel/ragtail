<p align="center">
  <img src="src/ragtail/ragtail_admin/static/icons/logo.svg" alt="Ragtail logo" width="160">
</p>

# Ragtail

> **Alpha** — Ragtail is in early development. APIs, database schema, and admin behaviour may change between releases; expect breaking changes until a stable 1.0.

Ragtail is a Wagtail-inspired CMS built on [Oxyde ORM](https://oxyde.fatalyst.dev/) and FastAPI. It ships with:

- hierarchical `Page` model
- locale-aware pages for multilingual sites
- named navigation menus with nested menu items
- JSON API for pages and menus at `/api/cms/` (enabled by default)
- HTML page delivery via optional Jinja2 or PyJSX template renderer
- **Wagtail-style admin** with login, page explorer, page editor, and image library (PyJSX UI)
- image library with `ImageField`, focal points, and renditions (Pillow included)
- **StreamField** — Wagtail-style content blocks (Markdown, HTML, images, struct blocks, custom templates)
- optional legacy `oxyde-admin` CRUD integration

Documents, workflows and role-based permissions are left for later iterations.

## Installation

### As a library

```bash
uv add "ragtail[jinja] @ git+https://github.com/glanzel/ragtail.git"
```

Initialize Oxyde configuration in your project directory (skip if `oxyde_config.py` already exists):

```bash
uv run oxyde init
```

Edit `oxyde_config.py` and add `ragtail.models` to `MODELS`, for example:

```python
MODELS = ["models", "ragtail.models"]
```

Quick start — mount into an existing FastAPI-Oxyde app:

```python
from fastapi import FastAPI
from oxyde_config import DATABASES
from ragtail import FastAPICMS

cms = FastAPICMS(secret_key="change-me")
app = FastAPI(lifespan=cms.lifespan(**DATABASES))
cms.mount(app)
```

Create the database, apply migrations, add locale and add a staff user (reads `DATABASES` from `oxyde_config.py` automatically):

```bash
uv run ragtail-seeddb \
  --language-code de \
  --display-name Deutsch \
  --username admin \
  --email admin@example.com \
  --password secret \
  --noinput
```

Open [http://localhost:8000/admin/](http://localhost:8000/admin/) for the CMS admin.

### Set up Pages

Custom page type with its own template:

```python
from oxyde import Field
from ragtail import Page, register_page_model

@register_page_model
class ContentPage(Page):
    body: str | None = Field(default=None, db_type="TEXT")
```

Published pages are available as JSON at `/api/cms/pages/{path}` — for example `GET /api/cms/pages/about/` returns `content_type`, `body`, and other fields. Use `?language=de` to resolve a specific locale. Menus: `GET /api/cms/menus/{slug}`.

### Set up Templates (optional)

```python
from ragtail import FastAPICMS, Jinja2Renderer

cms = FastAPICMS(
    secret_key="change-me",
    template_engine=Jinja2Renderer("templates"),
)
```

Default page template (`templates/page.html`):

```html
<h1>{{ page.title }}</h1>
```

```html
<!-- templates/content_page.html -->
<h1>{{ page.title }}</h1>
<div>{{ page.body }}</div>
```

## Documentation


| Topic                                  |                                                          |
| -------------------------------------- | -------------------------------------------------------- |
| [Installation](docs/installation.md)   | Dependencies, migrations, admin user, env vars, Tailwind |
| [FastAPI integration](docs/fastapi.md) | `FastAPICMS`, `create_app`, renderers                    |
| [Models](docs/models.md)               | `Page`, `Locale`, `Menu`, creating pages                 |
| [Images](docs/images.md)               | Image library, `ImageField`, renditions, focal points    |
| [StreamField](docs/streamfield.md)     | Content blocks, struct blocks, custom templates           |
| [Admin](docs/admin.md)                 | Wagtail-style CMS UI, rich text                          |
| [Routing](docs/routing.md)             | Multilingual URL resolution                              |
| [Menus](docs/menus.md)                 | Menu trees and API                                       |
| [Demo](docs/demo.md)                   | Runnable example app and Docker                          |


### Local development / testing

Library tests and the runnable demo are separate: pytest runs from the repository root; the demo is a small project in `examples/demo/` with its own `oxyde_config.py` and local `ragtail` dependency.Install
```bash
make install
```

Create and run the demo
```bash
make run-demo
```
localhost:8000 (login : admin / pw: admin)
