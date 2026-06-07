# Oxytail Demo

Runnable demo site with:

- **Wagtail-style admin** at `/admin/` (login: `admin` / `admin`)
- **PyJSX HTML rendering** for the public site
- SQLite database at `oxytail.db` (created on first run)

## Run

```bash
pip install -e ".[demo]"
npm install && npm run build:css   # only needed after template/CSS changes
python examples/demo/main.py
```

Or with uvicorn:

```bash
uvicorn examples.demo.main:app --reload
```

- Public site: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/
