from pathlib import Path

import pytest

from ragtail.db import load_app_databases


def test_load_app_databases_from_cwd(tmp_path: Path, oxyde_config) -> None:
    database_url = oxyde_config(f"sqlite:///{tmp_path / 'app.db'}")
    assert load_app_databases() == {"default": database_url}


def test_load_app_databases_without_config_raises(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    with pytest.raises(RuntimeError, match="oxyde init"):
        load_app_databases()
