#!/usr/bin/env python3
from __future__ import annotations

import importlib
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def setup_db() -> tuple[str, int]:
    import asyncio

    from oxyde import create_tables, db
    from oxytail.auth import ensure_superuser
    from oxytail.models import Locale
    from oxytail.pages import create_page
    from oxytail.wagtail_admin.services import ensure_root_page

    demo_dir = ROOT / "examples" / "demo"
    sys.path.insert(0, str(demo_dir))
    sys.path.insert(0, str(ROOT / "src"))
    from oxytail.wagtail_admin.registry import clear_page_form_fields

    clear_page_form_fields()
    importlib.import_module("admin_setup")

    async def _setup() -> tuple[str, int]:
        tmp = tempfile.mkdtemp()
        database_url = f"sqlite:///{Path(tmp) / 't.db'}"
        await db.init(default=database_url)
        connection = await db.get_connection("default")
        await create_tables(connection)
        await ensure_superuser(username="admin", password="admin")
        locale = await Locale.objects.create(
            language_code="en",
            display_name="English",
            is_default=True,
            is_active=True,
        )
        home = await ensure_root_page(locale)
        about = await create_page(
            title="About",
            slug="about",
            parent=home,
            locale=locale,
            live=True,
            body="Hello **world**",
        )
        assert about.id is not None
        return database_url, about.id

    return asyncio.run(_setup())


def main() -> int:
    from playwright.sync_api import sync_playwright

    database_url, page_id = setup_db()
    env = {
        **os.environ,
        "OXYTAIL_DATABASE_URL": database_url,
        "PYTHONPATH": f"{ROOT / 'src'}:{ROOT / 'examples' / 'demo'}",
    }
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "examples.demo.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8765",
        ],
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(2)
    errors: list[str] = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.on("console", lambda msg: errors.append(f"console:{msg.type}:{msg.text}"))
            page.on("pageerror", lambda err: errors.append(f"pageerror:{err}"))
            page.goto("http://127.0.0.1:8765/admin/login/", wait_until="networkidle")
            page.fill("input[name=username]", "admin")
            page.fill("input[name=password]", "admin")
            page.click("button[type=submit]")
            page.wait_for_load_state("networkidle")
            page.goto(
                f"http://127.0.0.1:8765/admin/pages/{page_id}/edit/",
                wait_until="networkidle",
            )
            page.wait_for_timeout(4000)
            button_count = page.locator("[data-richtext-toolbar] [data-action]").count()
            prose_count = page.locator(".ProseMirror").count()
            ready = page.locator("[data-richtext]").get_attribute("data-richtext-ready")
            toolbar_html = page.locator("[data-richtext-toolbar]").inner_html()
            print(f"buttons={button_count}")
            print(f"prosemirror={prose_count}")
            print(f"ready={ready}")
            print(f"toolbar_html={toolbar_html[:500]!r}")
            if errors:
                print("errors:")
                for error in errors:
                    print(f"  {error}")
            browser.close()
            return 0 if button_count > 0 and prose_count > 0 else 1
    finally:
        proc.terminate()
        proc.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
