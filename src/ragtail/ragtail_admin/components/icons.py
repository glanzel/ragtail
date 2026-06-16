from __future__ import annotations

from pyjsx.jsx import HTMLDontEscape

_ICON = (
    '<svg class="inline-block h-4 w-4 shrink-0 align-text-top" '
    'viewBox="0 0 16 16" aria-hidden="true">{body}</svg>'
)


def IconHome(children=None) -> HTMLDontEscape:
    return HTMLDontEscape(
        _ICON.format(
            body='<path fill="currentColor" d="M8 1.5 1 7.5v7h4.5v-4.5H10.5V14.5H15v-7L8 1.5Z"/>'
        )
    )


def IconDocEmptyInverse(children=None) -> HTMLDontEscape:
    return HTMLDontEscape(
        _ICON.format(
            body=(
                '<path fill="currentColor" '
                'd="M3 1.5h7.5L13.5 5v9.5H3V1.5Zm7 0V5h3.5L10 1.5ZM4.5 7h7v1h-7V7Zm0 2.5h7v1h-7v-1Zm0 2.5h5v1h-5v-1Z"/>'
            )
        )
    )


def IconFolderOpenInverse(children=None) -> HTMLDontEscape:
    return HTMLDontEscape(
        _ICON.format(
            body=(
                '<path fill="currentColor" '
                'd="M1.5 3.5h4.2l1.3 1.5H14.5V13H1.5V3.5Zm2 2v6.5h9V6.5H5.4L4.1 5H3.5v.5Z"/>'
            )
        )
    )


def IconGlobe(children=None) -> HTMLDontEscape:
    return HTMLDontEscape(
        _ICON.format(
            body=(
                '<path fill="currentColor" '
                'd="M8 1.5a6.5 6.5 0 1 0 0 13 6.5 6.5 0 0 0 0-13Zm5.1 3H9.6a10.7 10.7 0 0 1 0-3h3.5a5.5 5.5 0 0 1 2.1 1.4l-.1.1ZM8 3a9.2 9.2 0 0 0-1.2 3h2.4A9.2 9.2 0 0 0 8 3Zm-2.4 4a9.2 9.2 0 0 0 0 3h2.4a9.2 9.2 0 0 0 0-3H5.6Zm0 4.5a9.2 9.2 0 0 0 1.2 3 9.2 9.2 0 0 0-1.2-3Zm2.4 3a9.2 9.2 0 0 0 1.2-3H6.8a9.2 9.2 0 0 0 1.2 3ZM11.2 11a9.2 9.2 0 0 0 1.2 3 9.2 9.2 0 0 0-1.2-3Zm2.4-1.5h3.5a5.5 5.5 0 0 1-2.1 1.4H13.6a10.7 10.7 0 0 0 0-3h3.5a5.5 5.5 0 0 1 2.1 1.4l-.1.1Z"/>'
            )
        )
    )


def IconMenu(children=None) -> HTMLDontEscape:
    return HTMLDontEscape(
        _ICON.format(
            body='<path fill="currentColor" d="M2 3.5h12v2H2v-2Zm0 4h12v2H2v-2Zm0 4h12v2H2v-2Z"/>'
        )
    )


def IconUsers(children=None) -> HTMLDontEscape:
    return HTMLDontEscape(
        _ICON.format(
            body=(
                '<path fill="currentColor" '
                'd="M8 8.5a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM3 13.5c0-2.2 2.2-3.5 5-3.5s5 1.3 5 3.5V15H3v-1.5ZM11.5 9a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Zm2.8 1.5c1.5.3 2.7 1.2 2.7 2.7V15h-2.1v-1.3c0-.9-.4-1.7-1.1-2.2Z"/>'
            )
        )
    )


_RICHTEXT_ICON = (
    '<svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{body}</svg>'
)


def RichtextIconBold(children=None) -> HTMLDontEscape:
    return HTMLDontEscape(
        _RICHTEXT_ICON.format(
            body='<path d="M6 4h8a4 4 0 0 1 0 8H6z"/><path d="M6 12h9a4 4 0 0 1 0 8H6z"/>'
        )
    )


def RichtextIconItalic(children=None) -> HTMLDontEscape:
    return HTMLDontEscape(
        _RICHTEXT_ICON.format(
            body=(
                '<line x1="19" y1="4" x2="10" y2="4"/>'
                '<line x1="14" y1="20" x2="5" y2="20"/>'
                '<line x1="15" y1="4" x2="9" y2="20"/>'
            )
        )
    )


def RichtextIconStrike(children=None) -> HTMLDontEscape:
    return HTMLDontEscape(
        _RICHTEXT_ICON.format(
            body=(
                '<path d="M16 4H9a3 3 0 0 0-2.83 4"/>'
                '<path d="M14 12a4 4 0 0 1 0 8H6"/>'
                '<line x1="4" y1="12" x2="20" y2="12"/>'
            )
        )
    )


def RichtextIconBulletList(children=None) -> HTMLDontEscape:
    return HTMLDontEscape(
        _RICHTEXT_ICON.format(
            body=(
                '<line x1="9" y1="6" x2="20" y2="6"/>'
                '<line x1="9" y1="12" x2="20" y2="12"/>'
                '<line x1="9" y1="18" x2="20" y2="18"/>'
                '<circle cx="4" cy="6" r="1.25" fill="currentColor" stroke="none"/>'
                '<circle cx="4" cy="12" r="1.25" fill="currentColor" stroke="none"/>'
                '<circle cx="4" cy="18" r="1.25" fill="currentColor" stroke="none"/>'
            )
        )
    )


def RichtextIconOrderedList(children=None) -> HTMLDontEscape:
    return HTMLDontEscape(
        _RICHTEXT_ICON.format(
            body=(
                '<line x1="10" y1="6" x2="20" y2="6"/>'
                '<line x1="10" y1="12" x2="20" y2="12"/>'
                '<line x1="10" y1="18" x2="20" y2="18"/>'
                '<path d="M4 6h1v4"/>'
                '<path d="M4 10h2"/>'
                '<path d="M5 18H4c0-1 1-2 2-2s1-1 1-2-1-2-2-2"/>'
            )
        )
    )


def RichtextIconBlockquote(children=None) -> HTMLDontEscape:
    return HTMLDontEscape(
        _RICHTEXT_ICON.format(
            body=(
                '<path d="M7 7h10v10H7z"/>'
                '<path d="M11 9v6"/>'
                '<path d="M7 9h1"/>'
                '<path d="M7 15h1"/>'
            )
        )
    )


def RichtextIconUndo(children=None) -> HTMLDontEscape:
    return HTMLDontEscape(
        _RICHTEXT_ICON.format(
            body=(
                '<path d="M3 7v6h6"/>'
                '<path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6.36 2.64L3 13"/>'
            )
        )
    )


def RichtextIconRedo(children=None) -> HTMLDontEscape:
    return HTMLDontEscape(
        _RICHTEXT_ICON.format(
            body=(
                '<path d="M21 7v6h-6"/>'
                '<path d="M3 17a9 9 0 0 1 9-9 9 9 0 0 1 6.36 2.64L21 13"/>'
            )
        )
    )


def IconPlus(children=None) -> HTMLDontEscape:
    return HTMLDontEscape(
        _ICON.format(body='<path fill="currentColor" d="M7 1.5h2v5h5v2h-5v5H7v-5h-5v-2h5v-5Z"/>')
    )


_LOGO_URL = "/admin/static/icons/logo.svg"


def RagtailLogoBird(children=None) -> HTMLDontEscape:
    return HTMLDontEscape(
        f'<img src="{_LOGO_URL}" alt="" style="width:56px;height:auto;display:block;margin:20px" aria-hidden="true" />'
    )


def RagtailLogoWordmark(children=None) -> HTMLDontEscape:
    return HTMLDontEscape(
        f'<img src="{_LOGO_URL}" alt="Ragtail" style="width:72px;height:auto;display:block;margin:10px" />'
    )
