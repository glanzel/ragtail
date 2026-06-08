from __future__ import annotations

from oxyde import create_tables

from oxyde.db.pool import AsyncDatabase


async def ensure_tables(database: AsyncDatabase) -> None:
    """Create model tables when missing; no-op when they already exist."""
    try:
        await create_tables(database)
    except RuntimeError as exc:
        if "already exists" not in str(exc).lower():
            raise
