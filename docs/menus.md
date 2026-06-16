# Menus

Menus can be maintained through the admin or created with Oxyde directly. A menu tree can be fetched as serializable nodes:

```python
from oxytail.menus import create_menu, create_menu_item, get_menu_tree

main = await create_menu(name="Main", slug="main", locale=en)
await create_menu_item(menu=main, label="About", page=about)

items = await get_menu_tree("main", language_code="en")
payload = [item.as_dict() for item in items]
```

JSON API: `GET /api/cms/menus/{slug}`.
