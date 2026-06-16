# Installation

## As a library

```bash
uv add oxytail
```

Optional extras:

```bash
uv add "oxytail[jinja]"   # Jinja2 templates
uv add "oxytail[admin]"   # legacy oxyde-admin CRUD
```

## Local development (this repository)

This project uses [uv](https://docs.astral.sh/uv/) for Python dependency management.

```bash
make install              # Python + npm deps, build CSS
make migrate              # create DB and apply migrations
make createsuperuser      # first CMS staff user
make dev                  # demo app with reload
```

Equivalent without make:

```bash
uv sync --locked --extra demo
npm install && npm run build:css
uv run oxytail-initdb --database-url sqlite://oxytail.db
uv run oxytail-createsuperuser
uv run uvicorn examples.demo.main:app --reload
```

One-shot first-time setup:

```bash
make setup   # install + migrate + createsuperuser
```

## First admin user

Like Django's `createsuperuser`:

```bash
make createsuperuser
```

Non-interactive:

```bash
make createsuperuser USERNAME=admin EMAIL=admin@example.com PASSWORD=secret NOINPUT=1
```

Or directly:

```bash
uv run oxytail-createsuperuser --username admin --email admin@example.com --password secret --noinput
```

Use `--update` (or `make createsuperuser UPDATE=1`) to reset an existing user's password.

Environment variables for scripted runs:

- `OXYTAIL_SUPERUSER_USERNAME`
- `OXYTAIL_SUPERUSER_EMAIL`
- `OXYTAIL_SUPERUSER_PASSWORD`

## Database migrations

Ragtail uses [Oxyde migrations](https://oxyde.fatalyst.dev/) (Django-style). Configuration lives in `oxyde_config.py`; migration files are in `migrations/`.

```bash
make migrate              # create DB file if needed, apply pending migrations
make makemigrations       # generate migration after model changes
make showmigrations       # list applied/pending migrations
```

Fresh database:

```bash
rm -f oxytail.db
make migrate
make createsuperuser
```

Programmatically:

```python
from oxyde import db
from oxytail.db import run_migrations

await db.init(default="sqlite://oxytail.db")
await run_migrations()
```

## Environment variables

- `OXYTAIL_DATABASE_URL` — database (default: `sqlite://oxytail.db`)
- `OXYTAIL_SECRET_KEY` — admin session secret

## Frontend assets (Tailwind CSS)

Admin and demo templates use [Tailwind CSS](https://tailwindcss.com/) utility classes in PyJSX components. Compiled CSS is committed, but after changing `.px` templates run:

```bash
npm install
npm run build:css
```
