from __future__ import annotations

from ragtail.streamfield import CharBlock, StructBlock, URLBlock


class HighlightBlock(CharBlock):
    """Example custom block via subclassing with a template."""

    template = '<mark class="bg-yellow-200 px-1">{value}</mark>'

    def __init__(self) -> None:
        super().__init__(name="highlight", label="Highlight")


class CtaButtonBlock(StructBlock):
    """Example button block with label + URL fields and custom HTML template."""

    def __init__(self) -> None:
        super().__init__(
            name="cta_button",
            label="Button / Link",
            fields={
                "label": CharBlock(name="label", label="Button text"),
                "url": URLBlock(name="url", label="Link URL"),
            },
            template=(
                '<a href="{url}" class="inline-block rounded-lg bg-teal-700 px-4 py-2 '
                'font-semibold text-white no-underline hover:opacity-90">{label}</a>'
            ),
        )
