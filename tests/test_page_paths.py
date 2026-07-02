from ragtail.models import Page
from ragtail.sites import compute_page_path


def test_compute_page_path_omits_homepage_slug_for_descendants() -> None:
    tree_root = Page(id=1, title="", slug="_tree_root_", content_type="tree_root", path="/_tree_root_/", depth=1)
    home = Page(id=2, title="Home", slug="home", parent_id=1, path="/", depth=2)
    assert compute_page_path(tree_root, "home", site_root_page_id=2) == "/home/"
    assert compute_page_path(home, "about", site_root_page_id=2) == "/about/"
    assert compute_page_path(home, "team", site_root_page_id=2) == "/team/"

    about = Page(id=3, title="About", slug="about", parent_id=2, path="/about/", depth=3)
    assert compute_page_path(about, "team", site_root_page_id=2) == "/about/team/"


def test_compute_page_path_for_homepage_child_section() -> None:
    home = Page(id=2, title="Home", slug="home", parent_id=1, path="/", depth=2)
    blog = Page(id=4, title="Blog", slug="blog", parent_id=2, path="/blog/", depth=3)
    assert compute_page_path(blog, "first-post", site_root_page_id=2) == "/blog/first-post/"
