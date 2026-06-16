# FastAPI integration

## Mount into an existing app

```python
from fastapi import FastAPI
from oxytail import FastAPICMS, PageView, PyJsxRenderer, register_page_view

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

After `make migrate` (or `uv run oxytail-initdb`), create a staff user:

```bash
make createsuperuser
# or: uv run oxytail-createsuperuser --username admin --email admin@example.com --password secret --noinput
```

Open http://localhost:8000/admin/ for the CMS admin. Public pages are served on `/`, JSON API at `/api/cms/…` — same app and database.

PyJSX component naming: content type `detail_page` → `detailPage(page, context)`.

### Admin only (like oxyde-admin)

```python
app.mount("/admin", cms.app)
```

## Greenfield app

```python
from oxytail.fastapi import create_app

app = create_app(
    database_url="sqlite://oxytail.db",
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
from oxytail.fastapi import create_app

app = create_app(
    database_url="sqlite://oxytail.db",
    renderer=my_html_renderer,
    mount_wagtail_admin=True,
)
```

See [Demo application](demo.md) for a full PyJSX setup.

## Jinja2 templates

```bash
uv add "oxytail[jinja]"
```

```python
from oxytail import FastAPICMS, Jinja2Renderer

cms = FastAPICMS(
    secret_key="change-me",
    template_engine=Jinja2Renderer("templates"),
)
```
