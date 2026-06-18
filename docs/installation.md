# Installation

## As a library

```bash
uv add ragtail
```

Initialize Oxyde configuration in your project directory (skip if `oxyde_config.py` already exists):

```bash
uv run oxyde init
```

Add `ragtail.models` to `MODELS` in `oxyde_config.py`.

Optional extras:

```bash
uv add "ragtail[jinja]"   # Jinja2 templates
uv add "ragtail[admin]"   # legacy oxyde-admin CRUD
```

## Local development (this repository)

The **library** (tests, `make makemigrations`) uses the root `pyproject.toml`. Ragtail CMS migrations live inside the installed `ragtail` package; `ragtail-makemigrations` writes there. The **demo app** in `examples/demo/` has its own `oxyde_config.py` for database settings only.

```bash
make install              # root + demo Python envs, npm, build CSS
make migrate              # from examples/demo (ragtail-initdb)
make createsuperuser      # first CMS staff user
make run-demo             # uvicorn from examples/demo
```

Equivalent without make:

```bash
uv sync --locked
cd examples/demo && uv sync --locked
npm install && npm run build:css   # from repository root
cd examples/demo
uv run ragtail-initdb
uv run ragtail-createsuperuser
uv run uvicorn main:app --reload
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
make migrate              # create DB and apply migrations
make makemigrations       # generate migration files in the ragtail package
make showmigrations       # list package migrations (from examples/demo)
```

Fresh database:

```bash
rm -f ragtail.db
make migrate
make createsuperuser
```

Programmatically (after `await db.init(**DATABASES)` from your `oxyde_config.py`):

```python
from oxyde import db
from oxyde_config import DATABASES
from ragtail.db import run_migrations

await db.init(**DATABASES)
await run_migrations()
```

## Configuration

Database connections are read from `oxyde_config.py` in the **current working directory** (your app project, not the installed `ragtail` package). CLI commands (`ragtail-initdb`, `ragtail-seeddb`, `ragtail-createsuperuser`) use `DATABASES` automatically.

## Environment variables

- `RAGTAIL_SECRET_KEY` — admin session secret

## Frontend assets (Tailwind CSS)

Admin and demo templates use [Tailwind CSS](https://tailwindcss.com/) utility classes in PyJSX components. Compiled CSS is committed, but after changing `.px` templates run:

```bash
npm install
npm run build:css
```
