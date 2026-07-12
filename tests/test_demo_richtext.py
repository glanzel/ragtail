import importlib
import sys
from pathlib import Path

import pytest


def test_demo_registers_richtext_body_field() -> None:
    demo_dir = Path(__file__).resolve().parents[1] / "examples" / "demo"
    sys.path.insert(0, str(demo_dir))
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

    from ragtail.page_types import clear_page_models, get_page_form_fields_for

    clear_page_models()
    if "pages" in sys.modules:
        importlib.reload(sys.modules["pages"])
    else:
        importlib.import_module("pages")

    fields = get_page_form_fields_for("content_page")
    assert len(fields) == 3
    assert fields[0].name == "body"
    assert fields[0].widget == "richtext"
    assert fields[1].name == "hero_image"
    assert fields[1].widget == "image"
    assert fields[2].name == "content"
    assert fields[2].widget == "streamfield"

    clear_page_models()
