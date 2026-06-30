from __future__ import annotations

import hashlib
import io
import uuid
from pathlib import PurePosixPath

from PIL import Image as PILImage

from .filters import Filter, FilterOperationSpec
from .focal_point import FocalPoint, default_focal_point


class SourceImageIOError(Exception):
    """Raised when the original image cannot be read or processed."""


def compute_file_hash(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


def image_dimensions(data: bytes) -> tuple[int, int, str]:
    pil_image = _open_pil(data)
    width, height = pil_image.size
    fmt = (pil_image.format or "JPEG").lower()
    if fmt == "jpg":
        fmt = "jpeg"
    return width, height, fmt


def _open_pil(data: bytes):
    try:
        return PILImage.open(io.BytesIO(data))
    except OSError as exc:
        raise SourceImageIOError(str(exc)) from exc


def generate_rendition_bytes(
    source_data: bytes,
    *,
    filter_spec: str,
    focal_point_x: float | None = None,
    focal_point_y: float | None = None,
) -> tuple[bytes, int, int, str]:
    filter_obj = Filter.from_spec(filter_spec)
    pil_image = _open_pil(source_data)
    if pil_image.mode not in {"RGB", "RGBA", "L"}:
        pil_image = pil_image.convert("RGB")

    fx, fy = focal_point_x, focal_point_y
    if fx is None or fy is None:
        fx, fy = default_focal_point()
    focal = FocalPoint(x=fx, y=fy)

    for operation in filter_obj.operations:
        pil_image = _apply_operation(pil_image, operation, focal)

    output_format = filter_obj.output_format or _default_output_format(pil_image)
    buffer = io.BytesIO()
    save_kwargs = _save_kwargs(output_format)
    pil_image.save(buffer, format=_pil_format_name(output_format), **save_kwargs)
    data = buffer.getvalue()
    return data, pil_image.width, pil_image.height, output_format


def _default_output_format(pil_image) -> str:
    fmt = (getil_format := getattr(pil_image, "format", None)) and getil_format.lower()
    if fmt in {"jpeg", "jpg", "png", "webp"}:
        return "jpeg" if fmt == "jpg" else fmt
    return "jpeg"


def _pil_format_name(output_format: str) -> str:
    return "JPEG" if output_format == "jpeg" else output_format.upper()


def _save_kwargs(output_format: str) -> dict:
    if output_format == "jpeg":
        return {"quality": 85, "optimize": True}
    if output_format == "webp":
        return {"quality": 85, "method": 4}
    return {}


def _apply_operation(pil_image, operation: FilterOperationSpec, focal: FocalPoint):
    if operation.operation == "format":
        return pil_image
    if operation.operation == "width":
        assert operation.width is not None
        return _scale_to_width(pil_image, operation.width)
    if operation.operation == "height":
        assert operation.height is not None
        return _scale_to_height(pil_image, operation.height)
    if operation.operation == "max":
        assert operation.width is not None and operation.height is not None
        return _scale_max(pil_image, operation.width, operation.height)
    if operation.operation == "min":
        assert operation.width is not None and operation.height is not None
        return _scale_min(pil_image, operation.width, operation.height)
    if operation.operation == "fill":
        assert operation.width is not None and operation.height is not None
        return _fill(pil_image, operation.width, operation.height, focal)
    msg = f"Unsupported operation: {operation.operation}"
    raise ValueError(msg)


def _scale_to_width(pil_image, target_width: int):
    if pil_image.width <= target_width:
        return pil_image.copy()
    ratio = target_width / pil_image.width
    target_height = max(1, round(pil_image.height * ratio))
    return pil_image.resize((target_width, target_height), resample=_resample())


def _scale_to_height(pil_image, target_height: int):
    if pil_image.height <= target_height:
        return pil_image.copy()
    ratio = target_height / pil_image.height
    target_width = max(1, round(pil_image.width * ratio))
    return pil_image.resize((target_width, target_height), resample=_resample())


def _scale_max(pil_image, max_width: int, max_height: int):
    ratio = min(max_width / pil_image.width, max_height / pil_image.height, 1.0)
    if ratio >= 1.0:
        return pil_image.copy()
    target_width = max(1, round(pil_image.width * ratio))
    target_height = max(1, round(pil_image.height * ratio))
    return pil_image.resize((target_width, target_height), resample=_resample())


def _scale_min(pil_image, min_width: int, min_height: int):
    ratio = max(min_width / pil_image.width, min_height / pil_image.height)
    target_width = max(1, round(pil_image.width * ratio))
    target_height = max(1, round(pil_image.height * ratio))
    return pil_image.resize((target_width, target_height), resample=_resample())


def _fill(pil_image, target_width: int, target_height: int, focal: FocalPoint):
    scale = max(target_width / pil_image.width, target_height / pil_image.height)
    scaled_width = max(1, round(pil_image.width * scale))
    scaled_height = max(1, round(pil_image.height * scale))
    scaled = pil_image.resize((scaled_width, scaled_height), resample=_resample())

    focal_x = int(focal.x * scaled_width)
    focal_y = int(focal.y * scaled_height)

    left = focal_x - target_width // 2
    top = focal_y - target_height // 2
    left = max(0, min(left, scaled_width - target_width))
    top = max(0, min(top, scaled_height - target_height))
    right = left + target_width
    bottom = top + target_height
    return scaled.crop((left, top, right, bottom))


def _resample():
    return PILImage.Resampling.LANCZOS


def build_original_path(filename: str) -> str:
    safe_name = PurePosixPath(filename).name.replace(" ", "_")
    unique = uuid.uuid4().hex[:12]
    return f"images/original_images/{unique}_{safe_name}"


def build_rendition_path(original_file: str, filter_spec: str, extension: str) -> str:
    stem = PurePosixPath(original_file).stem
    safe_spec = filter_spec.replace("|", ".")
    return f"images/renditions/{stem}.{safe_spec}.{extension}"
