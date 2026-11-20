from __future__ import annotations

from copy import copy, deepcopy
from typing import Any


class SfdPaint:
    """Type 3 layer fill/stroke settings; 0xFFFFFFFE denotes inherited colour."""

    fill: bool
    stroke: bool
    fill_first: bool
    fill_color: int
    fill_opacity: float
    stroke_color: int
    stroke_opacity: float
    stroke_width: float
    line_join: str
    line_cap: str
    pen_transform: tuple[float, ...]
    dash: tuple[int, ...]

    def __init__(
        self,
        fill: bool = True,
        stroke: bool = False,
        fill_first: bool = True,
        fill_color: int = 0xFFFFFFFE,
        fill_opacity: float = 1,
        stroke_color: int = 0xFFFFFFFE,
        stroke_opacity: float = 1,
        stroke_width: float = -1,
        line_join: str = 'inherited',
        line_cap: str = 'inherited',
        pen_transform: tuple[float, ...] = (1, 0, 0, 1),
        dash: tuple[int, ...] = (),
    ) -> None:
        self.fill = fill
        self.stroke = stroke
        self.fill_first = fill_first
        self.fill_color = fill_color
        self.fill_opacity = fill_opacity
        self.stroke_color = stroke_color
        self.stroke_opacity = stroke_opacity
        self.stroke_width = stroke_width
        self.line_join = line_join
        self.line_cap = line_cap
        self.pen_transform = pen_transform
        self.dash = dash

    def __copy__(self) -> SfdPaint:
        return SfdPaint(
            self.fill,
            self.stroke,
            self.fill_first,
            self.fill_color,
            self.fill_opacity,
            self.stroke_color,
            self.stroke_opacity,
            self.stroke_width,
            self.line_join,
            self.line_cap,
            self.pen_transform,
            self.dash,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdPaint:
        result = copy(self)
        memo[id(self)] = result
        result.fill = deepcopy(self.fill, memo)
        result.stroke = deepcopy(self.stroke, memo)
        result.fill_first = deepcopy(self.fill_first, memo)
        result.fill_color = deepcopy(self.fill_color, memo)
        result.fill_opacity = deepcopy(self.fill_opacity, memo)
        result.stroke_color = deepcopy(self.stroke_color, memo)
        result.stroke_opacity = deepcopy(self.stroke_opacity, memo)
        result.stroke_width = deepcopy(self.stroke_width, memo)
        result.line_join = deepcopy(self.line_join, memo)
        result.line_cap = deepcopy(self.line_cap, memo)
        result.pen_transform = deepcopy(self.pen_transform, memo)
        result.dash = deepcopy(self.dash, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdPaint):
            return NotImplemented
        return (
            self.fill == other.fill
            and self.stroke == other.stroke
            and self.fill_first == other.fill_first
            and self.fill_color == other.fill_color
            and self.fill_opacity == other.fill_opacity
            and self.stroke_color == other.stroke_color
            and self.stroke_opacity == other.stroke_opacity
            and self.stroke_width == other.stroke_width
            and self.line_join == other.line_join
            and self.line_cap == other.line_cap
            and self.pen_transform == other.pen_transform
            and self.dash == other.dash
        )

    def copy(self) -> SfdPaint:
        return copy(self)

    def deepcopy(self) -> SfdPaint:
        return deepcopy(self)
