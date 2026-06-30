from __future__ import annotations

from .focal_point import default_focal_point
from .models import Image
from .renditions import build_original_path, compute_file_hash, image_dimensions
from .storage import get_storage


async def create_image_from_upload(*, title: str, filename: str, data: bytes) -> Image:
    width, height, _fmt = image_dimensions(data)
    path = build_original_path(filename)
    storage = get_storage()
    await storage.save(path, data)

    fx, fy = default_focal_point()
    image = Image(
        title=title.strip() or filename,
        file=path,
        width=width,
        height=height,
        focal_point_x=fx,
        focal_point_y=fy,
        file_hash=compute_file_hash(data),
        file_size=len(data),
    )
    await image.save()
    return image


async def update_image_focal_point(image: Image, *, x: float, y: float) -> Image:
    image.focal_point_x = max(0.0, min(1.0, x))
    image.focal_point_y = max(0.0, min(1.0, y))
    await image.invalidate_renditions()
    await image.save()
    return image


async def delete_image(image: Image) -> None:
    storage = get_storage()
    await image.invalidate_renditions()
    if image.file:
        await storage.delete(image.file)
    await image.delete()
