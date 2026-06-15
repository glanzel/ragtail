import importlib
import sys
from pathlib import Path

import pytest


def test_demo_registers_richtext_body_field() -> None:
    demo_dir = Path(__file__).resolve().parents[1] / "examples" / "demo"
    sys.path.insert(0, str(demo_dir))

    from ragtail.page_types import clear_page_models, get_page_form_fields_for

    clear_page_models()
    pages = importlib.import_module("pages")
    importlib.reload(pages)

    fields = get_page_form_fields_for("content_page")
    assert len(fields) == 1
    assert fields[0].name == "body"
    assert fields[0].widget == "richtext"

    clear_page_models()
