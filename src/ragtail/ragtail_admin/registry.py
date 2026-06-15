from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    pass

WidgetType = Literal["text", "textarea", "richtext"]


@dataclass(frozen=True)
class PageFormField:
    """Extra page editor field, comparable to a Ragtail FieldPanel."""

    name: str
    label: str
    widget: WidgetType = "textarea"


def infer_widget_for_field(name: str, meta: object) -> WidgetType:
    if name == "body":
        return "richtext"
    python_type = getattr(meta, "python_type", None)
    if python_type is str and getattr(meta, "db_type", None) == "TEXT":
        return "textarea"
    return "text"


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
