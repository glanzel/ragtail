"""Oxyde configuration for the Ragtail demo app."""

from __future__ import annotations

import os
from pathlib import Path

from oxyde.migrations.utils import detect_dialect

BASE_DIR = Path(__file__).resolve().parent

DATABASES = {
    "default": os.environ.get(
        "RAGTAIL_DATABASE_URL",
        f"sqlite:///{BASE_DIR}/ragtail.db",
    ),
}

MODELS = ["pages", "ragtail.models"]

# Demo-local migrations only (Ragtail CMS schema ships in the ragtail package).
MIGRATIONS_DIR = "migrations"

DIALECT = detect_dialect(DATABASES["default"])
