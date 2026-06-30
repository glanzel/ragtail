from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

FilterOperation = Literal["width", "height", "max", "min", "fill", "format"]


@dataclass(frozen=True)
class FilterOperationSpec:
    operation: FilterOperation
    width: int | None = None
    height: int | None = None
    format: str | None = None


@dataclass(frozen=True)
class Filter:
    operations: tuple[FilterOperationSpec, ...]

    @classmethod
    def from_spec(cls, filter_spec: str) -> Filter:
        parts = [part.strip() for part in filter_spec.split("|") if part.strip()]
        if not parts:
            msg = "Filter spec cannot be empty"
            raise ValueError(msg)
        operations: list[FilterOperationSpec] = []
        for part in parts:
            operations.append(_parse_operation(part))
        return cls(operations=tuple(operations))

    @property
    def cache_key(self) -> str:
        return "|".join(_operation_cache_key(op) for op in self.operations)

    @property
    def output_format(self) -> str | None:
        for op in reversed(self.operations):
            if op.operation == "format" and op.format:
                return op.format
        return None


def _operation_cache_key(op: FilterOperationSpec) -> str:
    if op.operation == "format":
        return f"format-{op.format}"
    if op.width is not None and op.height is not None:
        return f"{op.operation}-{op.width}x{op.height}"
    if op.width is not None:
        return f"{op.operation}-{op.width}"
    if op.height is not None:
        return f"{op.operation}-{op.height}"
    return op.operation


_DIMENSION_RE = re.compile(
    r"^(width|height|max|min|fill)-(\d+)(?:x(\d+))?$",
    re.IGNORECASE,
)
_FORMAT_RE = re.compile(r"^format-(jpeg|jpg|png|webp)$", re.IGNORECASE)


def _parse_operation(part: str) -> FilterOperationSpec:
    format_match = _FORMAT_RE.match(part)
    if format_match:
        fmt = format_match.group(1).lower()
        if fmt == "jpg":
            fmt = "jpeg"
        return FilterOperationSpec(operation="format", format=fmt)

    match = _DIMENSION_RE.match(part)
    if not match:
        msg = f"Unsupported filter operation: {part}"
        raise ValueError(msg)

    operation = match.group(1).lower()  # type: ignore[assignment]
    width = int(match.group(2))
    height = int(match.group(3)) if match.group(3) else None

    if operation in {"max", "min", "fill"} and height is None:
        msg = f"Filter '{part}' requires width and height"
        raise ValueError(msg)

    return FilterOperationSpec(
        operation=operation,  # type: ignore[arg-type]
        width=width,
        height=height,
    )
