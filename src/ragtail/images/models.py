from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from oxyde import Field, Index, Model

from ..models import TimestampedModel
from .focal_point import FocalPoint, default_focal_point
from .filters import Filter
from .renditions import (
    SourceImageIOError,
    build_rendition_path,
    generate_rendition_bytes,
)
from .storage import get_storage


class Image(TimestampedModel):
    """CMS image with Wagtail-style focal point and renditions."""

    id: int | None = Field(default=None, db_pk=True)
    title: str = Field(max_length=255, db_index=True)
    file: str = Field(max_length=512)
    width: int = Field(default=0)
    height: int = Field(default=0)
    focal_point_x: float | None = Field(default=None)
    focal_point_y: float | None = Field(default=None)
    file_hash: str | None = Field(default=None, max_length=64)
    file_size: int | None = Field(default=None)

    class Meta:
        is_table = True
        table_name = "oxytail_images"

    @property
    def url(self) -> str:
        return get_storage().url(self.file)

    @property
    def alt(self) -> str:
        return self.title

    @property
    def focal_point(self) -> FocalPoint | None:
        return FocalPoint.from_image(self)

    async def get_rendition(self, filter_spec: str) -> Rendition:
        existing = await self.find_existing_rendition(filter_spec)
        if existing is not None:
            return existing
        return await self.create_rendition(filter_spec)

    async def find_existing_rendition(self, filter_spec: str) -> Rendition | None:
        cache_key = Filter.from_spec(filter_spec).cache_key
        if self.id is None:
            return None
        return await Rendition.objects.get_or_none(image_id=self.id, filter_spec=cache_key)

    async def create_rendition(self, filter_spec: str) -> Rendition:
        if self.id is None or not self.file:
            msg = "Cannot create a rendition for an unsaved image"
            raise ValueError(msg)

        storage = get_storage()
        try:
            source_data = await storage.open(self.file)
            data, width, height, output_format = generate_rendition_bytes(
                source_data,
                filter_spec=filter_spec,
                focal_point_x=self.focal_point_x,
                focal_point_y=self.focal_point_y,
            )
        except SourceImageIOError as exc:
            msg = f"Could not read source image: {exc}"
            raise SourceImageIOError(msg) from exc

        extension = "jpg" if output_format == "jpeg" else output_format
        path = build_rendition_path(self.file, Filter.from_spec(filter_spec).cache_key, extension)
        await storage.save(path, data)

        rendition = Rendition(
            image_id=self.id,
            filter_spec=Filter.from_spec(filter_spec).cache_key,
            file=path,
            width=width,
            height=height,
        )
        await rendition.save()
        rendition.image = self
        return rendition

    async def get_renditions(self, *filter_specs: str) -> dict[str, Rendition]:
        result: dict[str, Rendition] = {}
        for spec in filter_specs:
            result[spec] = await self.get_rendition(spec)
        return result

    async def invalidate_renditions(self) -> None:
        storage = get_storage()
        renditions = await Rendition.objects.filter(image_id=self.id).all()
        for rendition in renditions:
            await storage.delete(rendition.file)
            await rendition.delete()


class Rendition(Model):
    """Cached transformed version of an ``Image``."""

    id: int | None = Field(default=None, db_pk=True)
    image: Image | None = Field(default=None, db_on_delete="CASCADE")
    filter_spec: str = Field(max_length=255)
    file: str = Field(max_length=512)
    width: int = Field(default=0)
    height: int = Field(default=0)

    class Meta:
        is_table = True
        table_name = "oxytail_renditions"
        unique_together = [("image", "filter_spec")]
        indexes = [
            Index(("image", "filter_spec")),
        ]

    @property
    def url(self) -> str:
        return get_storage().url(self.file)

    @property
    def alt(self) -> str:
        if self.image is not None:
            return self.image.alt
        return ""

    @property
    def focal_point(self) -> FocalPoint | None:
        if self.image is None:
            return None
        return self.image.focal_point

    @property
    def background_position_style(self) -> str:
        focal = self.focal_point
        if focal is None:
            x, y = default_focal_point()
            return FocalPoint(x=x, y=y).background_position_style
        return focal.background_position_style


@dataclass(frozen=True)
class ImageFieldInfo:
    """Marker metadata for Image foreign keys on Page models."""

    default_renditions: tuple[str, ...] = ()


def ImageField(*, default: Any = None, renditions: tuple[str, ...] = (), **kwargs: Any):
    metadata = list(kwargs.pop("metadata", []))
    metadata.append(ImageFieldInfo(default_renditions=renditions))
    return Field(default=default, metadata=metadata)
