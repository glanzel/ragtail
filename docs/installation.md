# Installation

## As a library

```bash
uv add ragtail
```

Optional extras:

```bash
uv add "ragtail[jinja]"   # Jinja2 templates
uv add "ragtail[admin]"   # legacy oxyde-admin CRUD
```

## Local development (this repository)

This project uses [uv](https://docs.astral.sh/uv/) for Python dependency management.

```bash
make install              # Python + npm deps, build CSS
make migrate              # create DB and apply migrations
make createsuperuser      # first CMS staff user
make run-demo             # demo app with reload
```

Equivalent without make:

```bash
uv sync --locked --extra demo
npm install && npm run build:css
uv run ragtail-initdb --database-url sqlite://ragtail.db
uv run ragtail-createsuperuser
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
uv run ragtail-createsuperuser --username admin --email admin@example.com --password secret --noinput
```

Use `--update` (or `make createsuperuser UPDATE=1`) to reset an existing user's password.

Environment variables for scripted runs:

- `RAGTAIL_SUPERUSER_USERNAME`
- `RAGTAIL_SUPERUSER_EMAIL`
- `RAGTAIL_SUPERUSER_PASSWORD`

## Database migrations

Ragtail uses [Oxyde migrations](https://oxyde.fatalyst.dev/) (Django-style). On app startup, `cms.lifespan` applies pending migrations automatically. For offline/CI use:

```bash
make migrate              # create DB file if needed, apply pending migrations
make makemigrations       # generate migration after model changes
make showmigrations       # list applied/pending migrations
```

Fresh database:

```bash
rm -f ragtail.db
make migrate
make createsuperuser
```

Programmatically:

```python
from oxyde import db
from ragtail.db import run_migrations

await db.init(default="sqlite://ragtail.db")
await run_migrations()
```

## Environment variables

- `RAGTAIL_DATABASE_URL` — database (default: `sqlite://ragtail.db`)
- `RAGTAIL_SECRET_KEY` — admin session secret

## Frontend assets (Tailwind CSS)

Admin and demo templates use [Tailwind CSS](https://tailwindcss.com/) utility classes in PyJSX components. Compiled CSS is committed, but after changing `.px` templates run:

```bash
npm install
npm run build:css
```
