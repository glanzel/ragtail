"""Register demo-only admin extensions (TipTap rich text on Page.body)."""

from ragtail.wagtail_admin.registry import PageFormField, register_page_form_field

register_page_form_field(
    PageFormField(
        name="body",
        label="Content",
        widget="richtext",
    )
)
