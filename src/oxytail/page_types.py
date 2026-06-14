from __future__ import annotations

import re
from typing import Any, TypeVar

from fastapi import Request
from pydantic.fields import FieldInfo

from .models import Page
from .routing import RouteMatch
from .wagtail_admin.registry import PageFormField, infer_widget_for_field

T = TypeVar("T", bound=type[Page])

_PAGE_MODELS: dict[str, type[Page]] = {}
_DEFAULT_PAGE_MODEL: type[Page] = Page

BASE_PAGE_FIELD_NAMES = frozenset(
    {
        "id",
        "title",
        "slug",
        "path",
        "depth",
        "sort_order",
        "locale",
        "locale_id",
        "translation_key",
        "parent",
        "parent_id",
        "children",
        "content_type",
        "seo_title",
        "search_description",
        "live",
        "show_in_menus",
        "first_published_at",
        "last_published_at",
        "created_at",
        "updated_at",
    }
)


def class_to_content_type(class_name: str) -> str:
    """Map ``AboutPage`` to ``about_page`` (Wagtail-style snake_case)."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", class_name).lower()


def content_type_to_component_name(content_type: str) -> str:
    """Map ``about_page`` to ``aboutPage`` for PyJSX components."""
    parts = content_type.strip("_").split("_")
    if not parts or not parts[0]:
        return content_type
    head, *tail = parts
    return head.lower() + "".join(part.capitalize() for part in tail)


def _field_meta_from_info(field_info: FieldInfo) -> object:
    resolved_db_type = None
    for extra in field_info.metadata:
        resolved_db_type = getattr(extra, "db_type", None)
        if resolved_db_type is not None:
            break

    class _Meta:
        python_type = field_info.annotation
        db_type = resolved_db_type

    return _Meta()


def _typed_field_names(model_cls: type[Page]) -> list[str]:
    if model_cls is Page:
        return []
    own_names = set(getattr(model_cls, "__annotations__", {}))
    return [
        name
        for name in model_cls.model_fields
        if name in own_names and name not in BASE_PAGE_FIELD_NAMES
    ]


async def persist_page(page: Page) -> Page:
    """Save a typed page through the shared ``Page`` table."""
    model_cls = type(page)
    field_names = set(Page.model_fields) | set(model_cls.model_fields)

    if page.id is not None:
        stored = await Page.objects.get(id=page.id)
    else:
        stored = Page()

    for name in field_names:
        if name in {"id", "children"}:
            continue
        setattr(stored, name, getattr(page, name, None))

    await stored.save()
    return await cast_page(stored)


def _patch_typed_save(model_cls: type[Page]) -> None:
    async def typed_save(
        self: Page,
        *,
        client: Any = None,
        using: str | None = None,
        update_fields: set[str] | None = None,
    ) -> Page:
        _ = client, using, update_fields
        persisted = await persist_page(self)
        for name in type(self).model_fields:
            object.__setattr__(self, name, getattr(persisted, name))
        return self

    model_cls.save = typed_save  # type: ignore[method-assign]


def register_page_model(model_cls: T) -> T:
    """Register a concrete Page subclass for routing, admin, and templates."""
    global _DEFAULT_PAGE_MODEL

    if model_cls is Page:
        msg = "Register concrete Page subclasses, not the base Page model"
        raise ValueError(msg)

    if not issubclass(model_cls, Page):
        msg = f"{model_cls.__name__} must subclass Page"
        raise TypeError(msg)

    content_type = class_to_content_type(model_cls.__name__)
    if content_type in _PAGE_MODELS:
        msg = f"Page model for content type '{content_type}' is already registered"
        raise ValueError(msg)

    model_cls._oxytail_content_type = content_type  # type: ignore[attr-defined]
    _PAGE_MODELS[content_type] = model_cls
    if _DEFAULT_PAGE_MODEL is Page:
        _DEFAULT_PAGE_MODEL = model_cls
    _patch_typed_save(model_cls)
    return model_cls


def get_page_model(content_type: str) -> type[Page]:
    return _PAGE_MODELS.get(content_type, Page)


def get_default_page_model() -> type[Page]:
    return _DEFAULT_PAGE_MODEL


def get_content_type(model_cls: type[Page]) -> str:
    return getattr(model_cls, "_oxytail_content_type", class_to_content_type(model_cls.__name__))


def get_all_page_models() -> list[type[Page]]:
    return list(_PAGE_MODELS.values())


def content_type_to_label(model_cls: type[Page]) -> str:
    """Human-readable label for a page model, e.g. ``ContentPage`` → ``Content page``."""
    name = model_cls.__name__
    if name.endswith("Page"):
        name = name[:-4]
    spaced = re.sub(r"(?<!^)(?=[A-Z])", " ", name).strip()
    return f"{spaced} page" if spaced else model_cls.__name__


def get_page_type_choices() -> list[tuple[str, str]]:
    """Return ``(content_type, label)`` pairs for registered page models."""
    return [(get_content_type(model), content_type_to_label(model)) for model in get_all_page_models()]


def get_page_model_or_404(content_type: str) -> type[Page]:
    model_cls = get_page_model(content_type.strip())
    if model_cls is Page:
        msg = f"Page type '{content_type}' is not registered"
        raise LookupError(msg)
    return model_cls


def clear_page_models() -> None:
    global _DEFAULT_PAGE_MODEL
    _PAGE_MODELS.clear()
    _DEFAULT_PAGE_MODEL = Page


async def cast_page(page: Page) -> Page:
    """Return a typed Page instance for the row's ``content_type``."""
    model_cls = get_page_model(page.content_type or "page")
    if model_cls is Page:
        return page
    if page.id is not None:
        row = await Page.objects.get_or_none(id=page.id)
        if row is not None:
            return model_cls.model_validate(row.model_dump())
    return model_cls.model_validate(page.model_dump())


def get_page_form_fields_for(content_type: str) -> list[PageFormField]:
    """Admin editor fields declared on the page model (excluding base Page fields)."""
    model_cls = get_page_model(content_type)
    if model_cls is Page:
        return []

    fields: list[PageFormField] = []
    for name in _typed_field_names(model_cls):
        field_info = model_cls.model_fields[name]
        fields.append(
            PageFormField(
                name=name,
                label=name.replace("_", " ").title(),
                widget=infer_widget_for_field(name, _field_meta_from_info(field_info)),
            )
        )
    return fields


def uses_richtext_for(content_type: str) -> bool:
    return any(field.widget == "richtext" for field in get_page_form_fields_for(content_type))
