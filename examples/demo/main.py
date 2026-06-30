"""Runnable Oxytail demo with Wagtail-style admin and PyJSX public templates."""

from __future__ import annotations

import os
from pathlib import Path

import pyjsx.auto_setup  # noqa: F401
from fastapi.staticfiles import StaticFiles
from oxyde_config import DATABASES

import site_setup  # noqa: F401 registers ContentPage and demo configuration

from ragtail.fastapi import create_app
from ragtail.templates import PyJsxRenderer

from seed import seed_if_empty

DEMO_DIR = Path(__file__).resolve().parent
SECRET_KEY = os.environ.get("RAGTAIL_SECRET_KEY", "ragtail-demo-secret-change-me")

app = create_app(
    **DATABASES,
    template_engine=PyJsxRenderer(components_module="site_templates.content_page"),
    mount_ragtail_admin=True,
    secret_key=SECRET_KEY,
    title="Oxytail Demo",
    startup_hook=seed_if_empty,
    media_root=str(DEMO_DIR / "media"),
)
app.mount("/static", StaticFiles(directory=DEMO_DIR / "static"), name="demo_static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
