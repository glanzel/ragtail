"""Oxyde ORM configuration for schema migrations."""

from __future__ import annotations

import os

from oxyde.migrations.utils import detect_dialect

DATABASE_URL = os.environ.get("OXYTAIL_DATABASE_URL", "sqlite://oxytail.db")

MODELS = ["oxytail.models"]

MIGRATIONS_DIR = "migrations"

DIALECT = detect_dialect(DATABASE_URL)

DATABASES = {
    "default": DATABASE_URL,
}
