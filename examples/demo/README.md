# Oxytail Demo

Self-contained demo project with its own `oxyde_config.py` and local editable `ragtail` dependency (`pyproject.toml`).

Features:

- **Wagtail-style admin** at `/admin/` (login: `admin` / `admin` after seeding)
- **Locales, menus & users** management in the admin sidebar
- **TipTap rich text** for page content (demo-only `body` field)
- **StreamField** on `ContentPage` — Markdown, HTML, image, highlight, and CTA button blocks (see `pages.py`, `stream_blocks.py`)
- **PyJSX HTML rendering** for the public site
- SQLite database at `ragtail.db` in this directory (created on first run)

## Run

From the repository root:

```bash
make install
make migrate
make createsuperuser
make run-demo
```

Or from this directory:

```bash
uv sync
uv run ragtail-initdb
uv run ragtail-createsuperuser
uv run uvicorn main:app --reload
```

Non-interactive seed (locale + admin user):

```bash
uv run ragtail-seeddb \
  --language-code de \
  --display-name Deutsch \
  --username admin \
  --email admin@example.com \
  --password secret \
  --noinput
```

The demo still seeds `admin` / `admin` on first run when the users table is empty.

- Public site: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

## Configuration

`oxyde_config.py` in this directory defines `DATABASES` and `MODELS` (`pages`, `ragtail.models`). CMS schema migrations ship with the installed `ragtail` package and are applied by `ragtail-initdb` / app startup — not from this `migrations/` folder unless you add demo-specific models later.

Optional environment variables:

- `RAGTAIL_DATABASE_URL` — overrides the default SQLite path in `oxyde_config.py`
- `RAGTAIL_SECRET_KEY` — admin session secret

## Docker

From the repository root:

```bash
docker build -t ragtail-demo .
docker run --rm -p 8000:8000 -v ragtail-data:/data ragtail-demo
```

The SQLite database is stored in `/data/ragtail.db` inside the container.
