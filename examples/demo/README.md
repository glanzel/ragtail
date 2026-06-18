# Oxytail Demo

Runnable demo site with:

- **Wagtail-style admin** at `/admin/` (login: `admin` / `admin`)
- **Locales, menus & users** management in the admin sidebar
- **TipTap rich text** for page content (demo-only `body` field)
- **PyJSX HTML rendering** for the public site
- SQLite database at `ragtail.db` (created on first run)

## Run

```bash
make install
make migrate          # apply schema migrations
make createsuperuser  # first admin user (interactive)
make run-demo
```

Non-interactive (e.g. CI):

```bash
make createsuperuser USERNAME=admin EMAIL=admin@example.com PASSWORD=secret NOINPUT=1
```

Or manually:

```bash
uv sync --locked --extra demo --extra admin
npm install && npm run build:css   # only needed after template/CSS changes
uv run python examples/demo/main.py
```

The demo still seeds `admin` / `admin` on first run when the users table is empty.
For production, create users explicitly with `make createsuperuser` and avoid demo defaults.

Or with make / uvicorn:

```bash
make install
make run-demo
# uv run uvicorn examples.demo.main:app --reload
```

- Public site: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

## Docker

From the repository root:

```bash
docker build -t ragtail-demo .
docker run --rm -p 8000:8000 -v ragtail-data:/data ragtail-demo
```

The SQLite database is stored in `/data/ragtail.db` inside the container (configured in `oxyde_config.py`).
Override optional environment variables:

- `RAGTAIL_DATABASE_URL` — overrides the default URL in `oxyde_config.py`
- `RAGTAIL_SECRET_KEY` (admin session secret)
