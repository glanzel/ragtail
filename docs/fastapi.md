# FastAPI

Assumes Ragtail is mounted into a FastAPI app with an Oxyde database connection. For database / ORM setup scenarios see [Integrations](integrations.md).

## Mount into an existing app

```python
from fastapi import FastAPI
from ragtail import FastAPICMS, PageView, PyJsxRenderer, register_page_view

@register_page_view
class SitePageView(PageView):
    content_type = "page"

    async def get_context(self, request, page, route):
        return {}

cms = FastAPICMS(
    secret_key="change-me",
    template_engine=PyJsxRenderer(components_module="site_templates.page"),
)
app = FastAPI(lifespan=cms.lifespan("sqlite://app.db"))
cms.mount(app)
```

Create a staff user:

```bash
uv run ragtail-createsuperuser --username admin --email admin@example.com --password secret --noinput
```

Open `/admin/` for the CMS admin. Public pages are served on `/`, JSON API at `/api/cms/…`.

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
from ragtail.fastapi import create_app

app = create_app(
    database_url="sqlite://ragtail.db",
    renderer=my_html_renderer,
    mount_wagtail_admin=True,
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
