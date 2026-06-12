from __future__ import annotations

SEARCH_DESCRIPTION_MAX_LENGTH = 500


def normalize_search_description(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    return cleaned[:SEARCH_DESCRIPTION_MAX_LENGTH]


def search_description_error(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    if len(cleaned) > SEARCH_DESCRIPTION_MAX_LENGTH:
        return f"Meta description must be at most {SEARCH_DESCRIPTION_MAX_LENGTH} characters."
    return None
