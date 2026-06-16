# Wagtail-style admin

Enable the built-in admin with session login:

```python
from ragtail.fastapi import create_app
from ragtail.auth import ensure_superuser

app = create_app(
    database_url="sqlite://ragtail.db",
    mount_wagtail_admin=True,
    secret_key="replace-me",
)

# once, e.g. in startup:
await ensure_superuser(username="admin", password="admin")
```

For production, prefer `make createsuperuser` or `ragtail-createsuperuser` instead of hard-coded credentials.

## Features

- Sign-in screen styled like Wagtail
- Sidebar navigation (Dashboard, Pages, Menus, Locales)
- Page explorer with tree + child listing
- Page editor (title, slug, SEO, publish settings)
- Locale management (add a second language, creates root page)
- Menu builder (create menus and add page/URL items)
- Create / edit / delete pages

## Rich text body on `ContentPage`

Register a page model with a `body` field. Fields named `body` automatically use the TipTap rich text widget in the admin:

```python
from oxyde import Field
from ragtail import Page, register_page_model

@register_page_model
class ContentPage(Page):
    body: str | None = Field(default=None, db_type="TEXT")
```

See `examples/demo/pages.py`.

The legacy generic `oxyde-admin` CRUD remains available via `mount_admin=True` on `create_app` or the `[admin]` extra.
