# Demo application

A runnable demo with Wagtail-style admin and PyJSX public templates lives in `examples/demo/` as its own small project (`pyproject.toml`, `oxyde_config.py`, local editable `ragtail`).

```bash
make install
make migrate
make createsuperuser
make run-demo
```

Or from `examples/demo/`:

```bash
uv sync
uv run uvicorn main:app --reload
```

- Public site: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

The demo seeds `admin` / `admin` on first run when the users table is empty. For production, create users explicitly and avoid demo defaults.

## Docker

From the repository root:

```bash
make docker-build
make docker-run
# or:
docker build -t ragtail-demo .
docker run --rm -p 8000:8000 -v ragtail-data:/data ragtail-demo
```

The SQLite database is stored in `/data/ragtail.db` inside the container.

See also `examples/demo/README.md` for demo-specific details.
