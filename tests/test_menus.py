from dataclasses import dataclass

from ragtail.menus import build_menu_tree


@dataclass
class PageStub:
    url: str


@dataclass
class ItemStub:
    id: int
    label: str
    sort_order: int
    parent_id: int | None = None
    url: str | None = None
    page: PageStub | None = None
    open_in_new_tab: bool = False

    @property
    def href(self) -> str:
        if self.page is not None:
            return self.page.url
        return self.url or "#"


def test_build_menu_tree_nests_children() -> None:
    items = [
        ItemStub(id=1, label="Home", sort_order=0, page=PageStub("/")),
        ItemStub(id=2, label="About", sort_order=1, page=PageStub("/about/")),
        ItemStub(id=3, label="Team", sort_order=0, parent_id=2, page=PageStub("/about/team/")),
    ]

    tree = build_menu_tree(items)  # type: ignore[arg-type]

    assert [node.label for node in tree] == ["Home", "About"]
    assert tree[0].href == "/"
    assert tree[1].children[0].as_dict() == {
        "id": 3,
        "label": "Team",
        "href": "/about/team/",
        "open_in_new_tab": False,
        "children": [],
    }


def test_build_menu_tree_keeps_orphaned_items_visible() -> None:
    items = [
        ItemStub(id=10, label="External", sort_order=0, parent_id=99, url="https://example.com"),
    ]

    tree = build_menu_tree(items)  # type: ignore[arg-type]

    assert len(tree) == 1
    assert tree[0].href == "https://example.com"
