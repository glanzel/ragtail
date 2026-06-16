# Models

Ragtail provides Oxyde models in `ragtail.models`:

- `Locale`: active languages/locales, including the default locale
- `Page`: tree-structured page with `parent`, `path`, `depth`, `locale` and `translation_key`
- `Menu`: named menu per locale, for example `main` or `footer`
- `MenuItem`: nested menu entries pointing either to a `Page` or an external URL
- `User`: staff users for CMS admin login

After model changes, generate and apply migrations — see [Installation](installation.md#database-migrations).

## Creating pages

Use the helper service so `path`, `depth` and `translation_key` are filled consistently:

```python
from ragtail.pages import create_page, create_translation

home = await create_page(title="Home", slug="", locale=en, live=True)
about = await create_page(title="About", slug="about", parent=home, locale=en, live=True)
ueber_uns = await create_translation(about, title="Ueber uns", slug="ueber-uns", locale=de)
```
