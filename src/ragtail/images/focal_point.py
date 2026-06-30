from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FocalPoint:
    x: float
    y: float

    @classmethod
    def from_image(cls, image: object) -> FocalPoint | None:
        x = getattr(image, "focal_point_x", None)
        y = getattr(image, "focal_point_y", None)
        if x is None or y is None:
            return None
        return cls(x=float(x), y=float(y))

    @property
    def centroid(self) -> FocalPoint:
        return self

    @property
    def background_position_style(self) -> str:
        return f"background-position: {self.x * 100:.2f}% {self.y * 100:.2f}%;"

    def default_for_size(self, width: int, height: int) -> FocalPoint:
        _ = width, height
        return self


def default_focal_point() -> tuple[float, float]:
    return 0.5, 0.5
