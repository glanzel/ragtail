# Integration

## Installation

```bash
uv add oxytail
```

## Quick start

```python
from fastapi import FastAPI
from oxytail import FastAPICMS

cms = FastAPICMS(secret_key="change-me")
app = FastAPI(lifespan=cms.lifespan("sqlite://app.db"))
cms.mount(app)
```

```bash
uv run oxytail-createsuperuser --username admin --email admin@example.com --password secret --noinput
```

Open http://localhost:8000/admin/ for the CMS admin. Public pages are served on `/` from the same app and database.

Admin only (like oxyde-admin):

```python
app.mount("/admin", cms.app)
```

Custom page renderer:

```python
cms = FastAPICMS(secret_key="change-me", renderer=my_html_renderer)
```
