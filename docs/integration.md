# Integration

## Installation

```bash
uv add ragtail
```

## Quick start

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

`ContentPage` maps to template `content_page.html` (Jinja2) or PyJSX component `contentPage(page, context)`.

```bash
uv run ragtail-createsuperuser --username admin --email admin@example.com --password secret --noinput
```

Open http://localhost:8000/admin/ for the CMS admin. Public pages are served on `/`, JSON API at `/api/cms/…` — same app and database.

Jinja2 (optional extra):

```bash
uv add "ragtail[jinja]"
```

```python
from ragtail import Jinja2Renderer

cms = FastAPICMS(
    secret_key="change-me",
    template_engine=Jinja2Renderer("templates"),
)
```

Admin only (like oxyde-admin):

```python
app.mount("/admin", cms.app)
```
