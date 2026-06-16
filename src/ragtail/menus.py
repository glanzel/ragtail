from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .models import Locale, Menu, MenuItem, Page
from .routing import get_locale


def _relation_id(instance: Any, field_name: str) -> int | None:
    direct_value = getattr(instance, f"{field_name}_id", None)
    if direct_value is not None:
        return direct_value

    related = getattr(instance, field_name, None)
    if related is None:
        return None
    return getattr(related, "id", None)


@dataclass
class MenuItemNode:
    """Serializable menu tree node."""

    id: int | None
    label: str
    href: str
    open_in_new_tab: bool = False
    children: list["MenuItemNode"] = field(default_factory=list)

    @classmethod
    def from_item(cls, item: MenuItem) -> "MenuItemNode":
        return cls(
            id=item.id,
            label=item.label,
            href=item.href,
            open_in_new_tab=item.open_in_new_tab,
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "label": self.label,
            "href": self.href,
            "open_in_new_tab": self.open_in_new_tab,
            "children": [child.as_dict() for child in self.children],
        }


def build_menu_tree(items: list[MenuItem]) -> list[MenuItemNode]:
    """Build a nested menu tree from flat MenuItem records."""

    nodes: dict[int, MenuItemNode] = {}
    roots: list[MenuItemNode] = []
    pending_children: dict[int, list[MenuItemNode]] = {}

    for item in items:
        node = MenuItemNode.from_item(item)
        item_id = item.id
        if item_id is not None:
            nodes[item_id] = node

        for pending in pending_children.pop(item_id, []):
            node.children.append(pending)

        parent_id = _relation_id(item, "parent")
        if parent_id is None:
            roots.append(node)
        elif parent_id in nodes:
            nodes[parent_id].children.append(node)
        else:
            pending_children.setdefault(parent_id, []).append(node)

    roots.extend(child for children in pending_children.values() for child in children)
    return roots


async def create_menu(
    *,
    name: str,
    slug: str,
    locale: Locale,
    is_active: bool = True,
) -> Menu:
    return await Menu.objects.create(
        name=name,
        slug=slug,
        locale_id=locale.id,
        is_active=is_active,
    )


async def create_menu_item(
    *,
    menu: Menu,
    label: str,
    parent: MenuItem | None = None,
    page: Page | None = None,
    url: str | None = None,
    sort_order: int = 0,
    is_active: bool = True,
    open_in_new_tab: bool = False,
) -> MenuItem:
    return await MenuItem.objects.create(
        menu_id=menu.id,
        parent_id=parent.id if parent is not None else None,
        page_id=page.id if page is not None else None,
        label=label,
        url=url,
        sort_order=sort_order,
        is_active=is_active,
        open_in_new_tab=open_in_new_tab,
    )


async def _hydrate_page_links(items: list[MenuItem]) -> list[MenuItem]:
    page_ids = sorted(
        {
            page_id
            for item in items
            if (page_id := _relation_id(item, "page")) is not None
        }
    )
    if not page_ids:
        return items

    pages = await Page.objects.filter(id__in=page_ids).all()
    pages_by_id = {page.id: page for page in pages}
    for item in items:
        page_id = _relation_id(item, "page")
        if page_id in pages_by_id:
            item.page = pages_by_id[page_id]
    return items


async def get_menu(slug: str, *, language_code: str | None = None) -> Menu | None:
    locale = await get_locale(language_code)
    if locale is None:
        return None
    return await Menu.objects.filter(slug=slug, locale_id=locale.id, is_active=True).first()


async def get_menu_tree(slug: str, *, language_code: str | None = None) -> list[MenuItemNode]:
    menu = await get_menu(slug, language_code=language_code)
    if menu is None:
        return []

    items = (
        await MenuItem.objects.filter(menu_id=menu.id, is_active=True)
        .order_by("parent_id", "sort_order", "id")
        .all()
    )
    items = await _hydrate_page_links(items)
    return build_menu_tree(items)
