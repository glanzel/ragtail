import importlib
import sys
from pathlib import Path

import pytest


def test_demo_registers_richtext_body_field() -> None:
    demo_dir = Path(__file__).resolve().parents[1] / "examples" / "demo"
    sys.path.insert(0, str(demo_dir))
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

    from oxytail.wagtail_admin.registry import clear_page_form_fields, get_page_form_fields

    clear_page_form_fields()
    admin_setup = importlib.import_module("admin_setup")
    importlib.reload(admin_setup)

    fields = get_page_form_fields()
    assert len(fields) == 1
    assert fields[0].name == "body"
    assert fields[0].widget == "richtext"

    clear_page_form_fields()
