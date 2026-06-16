from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

WidgetType = Literal["text", "textarea", "richtext"]


@dataclass(frozen=True)
class PageFormField:
    """Extra page editor field, comparable to a Wagtail FieldPanel."""

    name: str
    label: str
    widget: WidgetType = "textarea"


_page_form_fields: list[PageFormField] = []


def register_page_form_field(field: PageFormField) -> PageFormField:
    if any(existing.name == field.name for existing in _page_form_fields):
        msg = f"Page form field '{field.name}' is already registered"
        raise ValueError(msg)
    _page_form_fields.append(field)
    return field


def get_page_form_fields() -> list[PageFormField]:
    return list(_page_form_fields)


def uses_richtext() -> bool:
    return any(field.widget == "richtext" for field in _page_form_fields)


def clear_page_form_fields() -> None:
    """Reset registered fields (mainly for tests)."""
    _page_form_fields.clear()
