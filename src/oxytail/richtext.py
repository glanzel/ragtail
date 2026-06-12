from __future__ import annotations

import re

import bleach
from markdown_it import MarkdownIt

_md = MarkdownIt("commonmark", {"html": False}).enable("strikethrough")

_DANGEROUS_TAG_NAMES = ("script", "iframe", "object", "embed", "form", "meta", "link", "base")
_DANGEROUS_TAG_PATTERNS = tuple(
    re.compile(
        rf"<{tag}\b[^>]*>.*?</{tag}>",
        re.IGNORECASE | re.DOTALL,
    )
    for tag in _DANGEROUS_TAG_NAMES
)
_SELF_CLOSING_DANGEROUS_TAG = re.compile(
    r"<(script|iframe|object|embed|meta|link|base)\b[^>]*/>",
    re.IGNORECASE,
)
_EVENT_HANDLER_ATTR = re.compile(
    r"""\s+on[a-z]+\s*=\s*("[^"]*"|'[^']*'|[^\s>]+)""",
    re.IGNORECASE,
)
_JAVASCRIPT_URL = re.compile(r"javascript\s*:", re.IGNORECASE)

_ALLOWED_TAGS = [
    "p",
    "br",
    "strong",
    "em",
    "b",
    "i",
    "u",
    "s",
    "del",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "ul",
    "ol",
    "li",
    "blockquote",
    "pre",
    "code",
    "a",
    "hr",
]
_ALLOWED_ATTRIBUTES = {"a": ["href", "title", "rel"]}


def sanitize_stored_body(body: str) -> str:
    """Remove dangerous HTML fragments from stored markdown without altering safe text."""
    cleaned = body
    for pattern in _DANGEROUS_TAG_PATTERNS:
        cleaned = pattern.sub("", cleaned)
    cleaned = _SELF_CLOSING_DANGEROUS_TAG.sub("", cleaned)
    cleaned = _EVENT_HANDLER_ATTR.sub("", cleaned)
    cleaned = _JAVASCRIPT_URL.sub("", cleaned)
    return cleaned


def _normalize_markdown_lines(body: str) -> str:
    normalized = body.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in normalized.split("\n")]
    return "\n".join(lines).strip()


def prepare_body_for_storage(body: str | None) -> str | None:
    """Store richtext body as submitted markdown, minus critical XSS payloads."""
    if not body:
        return None
    return sanitize_stored_body(_normalize_markdown_lines(body))


def sanitize_rendered_html(html: str) -> str:
    return bleach.clean(
        html,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRIBUTES,
        strip=True,
    )


def render_body(body: str | None) -> str:
    """Convert stored markdown to safe HTML for the public site."""
    if not body:
        return ""
    return sanitize_rendered_html(_md.render(body))
