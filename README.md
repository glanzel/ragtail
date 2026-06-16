<p align="center">
  <img src="src/ragtail/ragtail_admin/static/icons/logo.svg" alt="Ragtail logo" width="160">
</p>

# Ragtail

Ragtail is a Wagtail-inspired CMS built on [Oxyde ORM](https://oxyde.fatalyst.dev/) and FastAPI. It ships with:

- hierarchical `Page` model
- locale-aware pages for multilingual sites
- named navigation menus with nested menu items
- JSON API for pages and menus at `/api/cms/` (enabled by default)
- HTML page delivery via optional Jinja2 or PyJSX template renderer
- **Wagtail-style admin** with login, page explorer, and page editor (PyJSX UI)
- optional legacy `oxyde-admin` CRUD integration

StreamField-like content blocks, images/documents, workflows and role-based permissions are left for later iterations.

## Installation

### As a library

```bash
uv add "ragtail[jinja]"
```

Quick start — mount into an existing FastAPI-Oxyde app:

```python
from fastapi import FastAPI
from ragtail import FastAPICMS

cms = FastAPICMS(secret_key="change-me")
app = FastAPI(lifespan=cms.lifespan("sqlite://app.db"))
cms.mount(app)  # includes /api/cms/ JSON API by default
```

Create the database, apply migrations, and add a staff user:

```bash
uv run ragtail-createsuperuser --username admin --email admin@example.com --password secret --noinput
```

Open [http://localhost:8000/admin/](http://localhost:8000/admin/) for the CMS admin.

### Set up Pages

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

Custom page type with its own template:

```python
from oxyde import Field
from ragtail import Page, register_page_model

@register_page_model
class ContentPage(Page):
    body: str | None = Field(default=None, db_type="TEXT")
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
| [Admin](docs/admin.md)                 | Wagtail-style CMS UI, rich text                          |
| [Routing](docs/routing.md)             | Multilingual URL resolution                              |
| [Menus](docs/menus.md)                 | Menu trees and API                                       |
| [Demo](docs/demo.md)                   | Runnable example app and Docker                          |


### Local development

```bash
make install
make migrate
make createsuperuser
make run-demo
```

Or in one step: `make setup`.

