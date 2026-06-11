# Oxytail Demo

Runnable demo site with:

- **Wagtail-style admin** at `/admin/` (login: `admin` / `admin`)
- **Locales & menus** management in the admin sidebar
- **TipTap rich text** for page content (demo-only `body` field)
- **PyJSX HTML rendering** for the public site
- SQLite database at `oxytail.db` (created on first run)

## Run

```bash
uv sync --locked --extra demo
npm install && npm run build:css   # only needed after template/CSS changes
uv run python examples/demo/main.py
```

Or with make / uvicorn:

```bash
make install
make dev
# uv run uvicorn examples.demo.main:app --reload
```

- Public site: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

## Docker

From the repository root:

```bash
docker build -t oxytail-demo .
docker run --rm -p 8000:8000 -v oxytail-data:/data oxytail-demo
```

The SQLite database is stored in `/data/oxytail.db` inside the container.
Override optional environment variables:

- `OXYTAIL_DATABASE_URL` (default: `sqlite:////data/oxytail.db`)
- `OXYTAIL_SECRET_KEY` (admin session secret)
