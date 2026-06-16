from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pyjsx.auto_setup  # noqa: F401
from fastapi.responses import HTMLResponse


def html_response(component: Callable[..., Any], **context: Any) -> HTMLResponse:
    return HTMLResponse(f"{component(**context)}")
