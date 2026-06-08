from pathlib import Path


def test_admin_css_includes_richtext_toolbar_styles() -> None:
    css_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "oxytail"
        / "wagtail_admin"
        / "static"
        / "wagtail-admin.css"
    )
    css = css_path.read_text(encoding="utf-8")
    assert ".richtext-toolbar-btn" in css
    assert ".ProseMirror" in css


def test_richtext_bundle_is_self_contained() -> None:
    js_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "oxytail"
        / "wagtail_admin"
        / "static"
        / "richtext.js"
    )
    js = js_path.read_text(encoding="utf-8")
    assert len(js) > 100_000
    assert "esm.sh" not in js
    assert "jsdelivr" not in js
