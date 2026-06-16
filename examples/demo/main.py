"""Runnable Oxytail demo with Wagtail-style admin and PyJSX public templates."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pyjsx.auto_setup  # noqa: F401
from fastapi.staticfiles import StaticFiles

DEMO_DIR = Path(__file__).resolve().parent
ROOT = DEMO_DIR.parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(DEMO_DIR))

import admin_setup  # noqa: F401,E402 registers demo rich text field
import site_setup  # noqa: F401,E402 registers demo page views

from ragtail.fastapi import create_app  # noqa: E402
from ragtail.templates import PyJsxRenderer  # noqa: E402

from seed import seed_if_empty  # noqa: E402

DEFAULT_DB_PATH = DEMO_DIR / "ragtail.db"
DATABASE_URL = os.environ.get(
    "RAGTAIL_DATABASE_URL",
    f"sqlite:////{DEFAULT_DB_PATH}",
)
SECRET_KEY = os.environ.get("RAGTAIL_SECRET_KEY", "ragtail-demo-secret-change-me")

app = create_app(
    database_url=DATABASE_URL,
    template_engine=PyJsxRenderer(components_module="site_templates.page"),
    mount_wagtail_admin=True,
    secret_key=SECRET_KEY,
    title="Oxytail Demo",
    startup_hook=seed_if_empty,
)
app.mount("/static", StaticFiles(directory=DEMO_DIR / "static"), name="demo_static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
