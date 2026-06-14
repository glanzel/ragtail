# Integration

## Installation

```bash
uv add oxytail
```

## Quick start

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

```bash
uv run oxytail-createsuperuser --username admin --email admin@example.com --password secret --noinput
```

Open http://localhost:8000/admin/ for the CMS admin. Public pages are served on `/`, JSON API at `/api/cms/…` — same app and database.

PyJSX component naming: content type `detail_page` → `detailPage(page, context)`.

Jinja2 (optional extra):

```bash
uv add "oxytail[jinja]"
```

```python
from oxytail import Jinja2Renderer

cms = FastAPICMS(
    secret_key="change-me",
    template_engine=Jinja2Renderer("templates"),
)
```

Admin only (like oxyde-admin):

```python
app.mount("/admin", cms.app)
```
