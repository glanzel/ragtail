# FastAPI

Assumes Ragtail is mounted into a FastAPI app with an Oxyde database connection. For database / ORM setup scenarios see [Integrations](integrations.md).

## Mount into an existing app

```python
from fastapi import FastAPI
from oxyde import Field

from ragtail import FastAPICMS, Page, PyJsxRenderer, register_page_model

@register_page_model
class ContentPage(Page):
    body: str | None = Field(default=None, db_type="TEXT")

    async def get_context(self, request, route):
        return {}

cms = FastAPICMS(
    secret_key="change-me",
    template_engine=PyJsxRenderer(components_module="site_templates.content_page"),
)
app = FastAPI(lifespan=cms.lifespan("sqlite://app.db"))
cms.mount(app)
```

Create a staff user:

```bash
uv run ragtail-createsuperuser --username admin --email admin@example.com --password secret --noinput
```

Open `/admin/` for the CMS admin. The JSON API at `/api/cms/…` is mounted by default (`cms.mount(app)`); pass `api=False` to disable it. Public pages are served on `/`.

PyJSX component naming: content type `detail_page` → `detailPage(page, context)`.

### Admin only (like oxyde-admin)

```python
app.mount("/admin", cms.app)
```

Mount the admin sub-app without public page routes or JSON API (`cms.mount(app, pages=False, api=False)` is equivalent when you wire `cms.app` yourself).

## Greenfield app

```python
from ragtail.fastapi import create_app

app = create_app(
    database_url="sqlite://ragtail.db",
    mount_ragtail_admin=True,
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
from ragtail.fastapi import create_app

app = create_app(
    database_url="sqlite://ragtail.db",
    renderer=my_html_renderer,
    mount_ragtail_admin=True,
)
```

See [Demo application](demo.md) for a full PyJSX setup.

## Jinja2 templates

```bash
uv add "ragtail[jinja]"
```

```python
from ragtail import FastAPICMS, Jinja2Renderer

cms = FastAPICMS(
    secret_key="change-me",
    template_engine=Jinja2Renderer("templates"),
)
```
