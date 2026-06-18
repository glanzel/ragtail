from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

import pytest


@pytest.fixture
def oxyde_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Callable[[str], str]:
    """Write oxyde_config.py in a temp dir and chdir there for CLI/app tests."""

    def _configure(database_url: str) -> str:
        sys.modules.pop("oxyde_config", None)
        (tmp_path / "oxyde_config.py").write_text(
            f'DATABASES = {{"default": "{database_url}"}}\nMODELS = ["ragtail.models"]\n',
            encoding="utf-8",
        )
        monkeypatch.chdir(tmp_path)
        return database_url

    return _configure
