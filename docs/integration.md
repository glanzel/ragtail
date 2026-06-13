# Integration

## Installation

```bash
uv add oxytail
```

## Quick start

Mount Oxytail into your existing FastAPI app — same process, same database as your Oxyde models:

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from oxyde import db
from starlette.middleware.sessions import SessionMiddleware

from oxytail.db import prepare_sqlite_database, run_migrations
from oxytail.fastapi import create_cms_router
from oxytail.wagtail_admin import create_admin_router
from oxytail.wagtail_admin.router import AdminLoginRequired, STATIC_DIR, _login_url

DATABASE_URL = "sqlite://app.db"


@asynccontextmanager
async def lifespan(app: FastAPI):
    prepare_sqlite_database(DATABASE_URL)
    async with db.lifespan(default=DATABASE_URL):
        await run_migrations()
        yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(SessionMiddleware, secret_key="change-me")
app.mount("/admin/static", StaticFiles(directory=STATIC_DIR), name="oxytail_static")
app.include_router(create_admin_router(), prefix="/admin")


@app.exception_handler(AdminLoginRequired)
async def _admin_login(_: Request, exc: AdminLoginRequired) -> RedirectResponse:
    return RedirectResponse(_login_url(exc.next_url), status_code=303)


app.include_router(create_cms_router())  # last — catch-all for public pages
```

```bash
uv run oxytail-initdb --database-url sqlite://app.db
uv run oxytail-createsuperuser --username admin --email admin@example.com --password secret --noinput
```

Open http://localhost:8000/admin/ for the CMS admin. Public pages are served on `/` from the same app.

Add `oxytail.models` to your `oxyde_config.MODELS` if you use `oxyde makemigrations` for your own models. SQLite URLs use `sqlite://relative.db` or `sqlite:////absolute/path.db` (not Django's `sqlite:///…`).
