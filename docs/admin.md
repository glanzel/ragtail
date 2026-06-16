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

## Demo-only rich text (TipTap)

The core page editor intentionally has no body field. The demo registers a `body` rich text field (TipTap) similar to Wagtail's `RichTextField`:

```python
from ragtail.wagtail_admin.registry import PageFormField, register_page_form_field

register_page_form_field(
    PageFormField(name="body", label="Content", widget="richtext")
)
```

See `examples/demo/admin_setup.py`.

The legacy generic `oxyde-admin` CRUD remains available via `mount_admin=True` on `create_app` or the `[admin]` extra.
