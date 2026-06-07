"""Runnable Oxytail demo with Wagtail-style admin and PyJSX public templates."""

from __future__ import annotations

import sys
from pathlib import Path

import pyjsx.auto_setup  # noqa: F401
from fastapi.staticfiles import StaticFiles

DEMO_DIR = Path(__file__).resolve().parent
ROOT = DEMO_DIR.parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(DEMO_DIR))

from oxytail.fastapi import create_app  # noqa: E402

from renderer import create_site_renderer  # noqa: E402
from seed import seed_if_empty  # noqa: E402

DATABASE_URL = f"sqlite:///{DEMO_DIR / 'oxytail.db'}"

app = create_app(
    database_url=DATABASE_URL,
    renderer=create_site_renderer(),
    mount_wagtail_admin=True,
    secret_key="oxytail-demo-secret-change-me",
    title="Oxytail Demo",
    startup_hook=seed_if_empty,
)
app.mount("/static", StaticFiles(directory=DEMO_DIR / "static"), name="demo_static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
