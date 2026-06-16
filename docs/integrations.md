# Integrations

Ragtail stores CMS content in **Oxyde models** (`Page`, `Locale`, `Menu`, `User`, …). Your application code can keep its own data layer — the question is how the database connection is set up.

## Fall B: Existing app with another ORM (most common)

Typical setup: FastAPI + **SQLAlchemy**, Tortoise, raw `asyncpg`, etc. for your domain models, plus Ragtail for CMS content.

Ragtail does **not** use your ORM models. It opens its own Oxyde connection and creates its own tables via migrations. Your shop orders, user profiles, or whatever you already have are unaffected.

### Same database (recommended when possible)

Point Ragtail at the **same database** your app already uses — one PostgreSQL (or SQLite) instance, two ORMs side by side:

```python
# Your app already has something like:
# engine = create_async_engine(os.environ["DATABASE_URL"])

from ragtail import FastAPICMS

cms = FastAPICMS(secret_key=os.environ["RAGTAIL_SECRET_KEY"])
app = FastAPI(lifespan=cms.lifespan(os.environ["DATABASE_URL"]))
cms.mount(app)
```

Ragtail ships its migrations in the installed package at **`ragtail/migrations/`** (e.g. `0001_ragtail_initial`). They are applied automatically via `cms.lifespan` or `await run_migrations()` — independent of your app's `migrations/` directory.

Use the same URL for CLI tools:

```bash
uv run ragtail-createsuperuser --database-url "$DATABASE_URL" ...
```

**Note:** You now have two connection pools (your ORM + Oxyde). That is normal. Transactions are not shared across them unless you coordinate that yourself.

### Separate database

If you prefer isolation, give Ragtail its own URL:

```python
CMS_DATABASE_URL = os.environ["RAGTAIL_DATABASE_URL"]  # e.g. sqlite://ragtail.db

cms = FastAPICMS(secret_key=...)
app = FastAPI(lifespan=cms.lifespan(CMS_DATABASE_URL))
cms.mount(app)
```

Your app keeps `DATABASE_URL`; Ragtail uses `RAGTAIL_DATABASE_URL`. Deploy migrations and `createsuperuser` against the CMS URL only.

## Fall A: No existing database (greenfield)

FastAPI alone has no database. For a small site or prototype you can let Ragtail own everything:

```python
from ragtail import FastAPICMS

cms = FastAPICMS(secret_key="change-me")
app = FastAPI(lifespan=cms.lifespan("sqlite://ragtail.db"))
cms.mount(app)
```

Or use the bundled factory:

```python
from ragtail.fastapi import create_app

app = create_app(
    database_url="sqlite://ragtail.db",
    mount_ragtail_admin=True,
    secret_key="replace-me",
)
```

Migrations run on first app start. Create a staff user with `ragtail-createsuperuser` (see [Installation](installation.md)).

For a full PyJSX example, see [Demo](demo.md) and `examples/demo/`.

## Offline migrations (CI / Docker)

You do not need a separate `initdb` step before the first app start — the lifespan migrates automatically. For deploy pipelines that prepare the schema without running uvicorn:

```bash
uv run ragtail-initdb --database-url "$DATABASE_URL"
```

Same as `make migrate` in this repository.
