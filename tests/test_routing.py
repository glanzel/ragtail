from oxytail.routing import (
    join_page_path,
    localized_path,
    normalize_path,
    strip_locale_prefix,
)


def test_normalize_path_adds_slashes() -> None:
    assert normalize_path(None) == "/"
    assert normalize_path("") == "/"
    assert normalize_path("/") == "/"
    assert normalize_path("about") == "/about/"
    assert normalize_path("/about/team") == "/about/team/"


def test_join_page_path_builds_child_urls() -> None:
    assert join_page_path("/", "about") == "/about/"
    assert join_page_path("/about/", "team") == "/about/team/"
    assert join_page_path("/about", "/team/") == "/about/team/"


def test_strip_locale_prefix() -> None:
    assert strip_locale_prefix("/de/ueber-uns/", ["en", "de"]) == ("de", "/ueber-uns/")
    assert strip_locale_prefix("/en/", ["en", "de"]) == ("en", "/")
    assert strip_locale_prefix("/about/", ["en", "de"]) == (None, "/about/")


def test_localized_path_can_omit_default_language() -> None:
    assert localized_path("/about/", "en", default_language_code="en") == "/about/"
    assert localized_path("/about/", "de", default_language_code="en") == "/de/about/"
    assert (
        localized_path(
            "/about/",
            "en",
            default_language_code="en",
            prefix_default_language=True,
        )
        == "/en/about/"
    )
