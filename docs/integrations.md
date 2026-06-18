# Integrations

Ragtail stores CMS content in **Oxyde models** (`Page`, `Locale`, `Menu`, `User`, …). Your application code can keep its own data layer — the question is how the database connection is set up.

All Ragtail CLI tools and `cms.lifespan()` read `DATABASES` from **`oxyde_config.py` in your project directory** (run `oxyde init` once if the file does not exist yet).

## Fall B: Existing app with another ORM (most common)

Typical setup: FastAPI + **SQLAlchemy**, Tortoise, raw `asyncpg`, etc. for your domain models, plus Ragtail for CMS content.

Ragtail does **not** use your ORM models. It opens its own Oxyde connection and creates its own tables via migrations. Your shop orders, user profiles, or whatever you already have are unaffected.

### Same database (recommended when possible)

Point Ragtail at the **same database** your app already uses — one PostgreSQL (or SQLite) instance, two ORMs side by side. Set the same URL in `oxyde_config.py` `DATABASES`:

```python
# oxyde_config.py
DATABASES = {
    "default": "postgresql://user:pass@localhost/mydb",
}
MODELS = ["app.models", "ragtail.models"]
```

```python
from oxyde_config import DATABASES
from ragtail import FastAPICMS

cms = FastAPICMS(secret_key=os.environ["RAGTAIL_SECRET_KEY"])
app = FastAPI(lifespan=cms.lifespan(**DATABASES))
cms.mount(app)
```

Ragtail ships its migrations in the installed package at **`ragtail/migrations/`** (e.g. `0001_ragtail_initial`). They are applied automatically via `cms.lifespan` or `await run_migrations()` — independent of your app's `migrations/` directory.

CLI tools pick up the same config automatically:

```bash
uv run ragtail-createsuperuser --username admin --email admin@example.com --password secret --noinput
```

**Note:** You now have two connection pools (your ORM + Oxyde). That is normal. Transactions are not shared across them unless you coordinate that yourself.

### Separate database

If you prefer isolation, configure a dedicated alias or URL in `oxyde_config.py`:

```python
DATABASES = {
    "default": "postgresql://localhost/app",
    "cms": "sqlite:///ragtail.db",
}
```

Your app keeps its own connection; Ragtail uses `cms.lifespan(default=DATABASES["cms"])` or a single `default` entry for CMS-only deployments.

## Fall A: No existing database (greenfield)

FastAPI alone has no database. For a small site or prototype you can let Ragtail own everything:

```python
from oxyde_config import DATABASES
from ragtail import FastAPICMS

cms = FastAPICMS(secret_key="change-me")
app = FastAPI(lifespan=cms.lifespan(**DATABASES))
cms.mount(app)
```

Or use the bundled factory:

```python
from oxyde_config import DATABASES
from ragtail.fastapi import create_app

app = create_app(
    **DATABASES,
    mount_ragtail_admin=True,
    secret_key="replace-me",
)
```

Migrations run on first app start. Create a staff user with `ragtail-createsuperuser` (see [Installation](installation.md)).

For a full PyJSX example, see [Demo](demo.md) and `examples/demo/`.

## Offline migrations (CI / Docker)

You do not need a separate `initdb` step before the first app start — the lifespan migrates automatically. For deploy pipelines that prepare the schema without running uvicorn:

```bash
uv run ragtail-initdb
```

Same as `make migrate` in this repository. Run commands from the directory that contains `oxyde_config.py`.
