"""Oxyde ORM configuration for schema migrations."""

from __future__ import annotations

import os

from oxyde.migrations.utils import detect_dialect

DATABASE_URL = os.environ.get("RAGTAIL_DATABASE_URL", "sqlite://ragtail.db")

MODELS = ["ragtail.models"]

MIGRATIONS_DIR = "migrations"

DIALECT = detect_dialect(DATABASE_URL)

DATABASES = {
    "default": DATABASE_URL,
}
