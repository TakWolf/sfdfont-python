from __future__ import annotations

from copy import copy, deepcopy
from typing import Any


class SfdGradientStop:
    offset: float
    color: int
    opacity: float

    def __init__(
        self,
        offset: float = 0,
        color: int = 0,
        opacity: float = 1,
    ) -> None:
        self.offset = offset
        self.color = color
        self.opacity = opacity

    def __copy__(self) -> SfdGradientStop:
        return SfdGradientStop(
            self.offset,
            self.color,
            self.opacity,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdGradientStop:
        result = copy(self)
        memo[id(self)] = result
        result.offset = deepcopy(self.offset, memo)
        result.color = deepcopy(self.color, memo)
        result.opacity = deepcopy(self.opacity, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdGradientStop):
            return NotImplemented
        return self.offset == other.offset and self.color == other.color and self.opacity == other.opacity

    def copy(self) -> SfdGradientStop:
        return copy(self)

    def deepcopy(self) -> SfdGradientStop:
        return deepcopy(self)


class SfdGradient:
    start: tuple[float, float]
    end: tuple[float, float]
    radius: float
    spread: str
    stops: list[SfdGradientStop]

    def __init__(
        self,
        start: tuple[float, float] = (0, 0),
        end: tuple[float, float] = (1, 0),
        radius: float = 0,
        spread: str = 'pad',
        stops: list[SfdGradientStop] | None = None,
    ) -> None:
        self.start = start
        self.end = end
        self.radius = radius
        self.spread = spread
        self.stops = stops if stops is not None else []

    def __copy__(self) -> SfdGradient:
        return SfdGradient(
            self.start,
            self.end,
            self.radius,
            self.spread,
            self.stops,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdGradient:
        result = copy(self)
        memo[id(self)] = result
        result.start = deepcopy(self.start, memo)
        result.end = deepcopy(self.end, memo)
        result.radius = deepcopy(self.radius, memo)
        result.spread = deepcopy(self.spread, memo)
        result.stops = deepcopy(self.stops, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdGradient):
            return NotImplemented
        return (
            self.start == other.start
            and self.end == other.end
            and self.radius == other.radius
            and self.spread == other.spread
            and self.stops == other.stops
        )

    def copy(self) -> SfdGradient:
        return copy(self)

    def deepcopy(self) -> SfdGradient:
        return deepcopy(self)


class SfdPattern:
    glyph: str
    width: float
    height: float
    transform: tuple[float, ...]

    def __init__(
        self,
        glyph: str = '.notdef',
        width: float = 1000,
        height: float = 1000,
        transform: tuple[float, ...] = (1, 0, 0, 1, 0, 0),
    ) -> None:
        self.glyph = glyph
        self.width = width
        self.height = height
        self.transform = transform

    def __copy__(self) -> SfdPattern:
        return SfdPattern(
            self.glyph,
            self.width,
            self.height,
            self.transform,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdPattern:
        result = copy(self)
        memo[id(self)] = result
        result.glyph = deepcopy(self.glyph, memo)
        result.width = deepcopy(self.width, memo)
        result.height = deepcopy(self.height, memo)
        result.transform = deepcopy(self.transform, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdPattern):
            return NotImplemented
        return (
            self.glyph == other.glyph
            and self.width == other.width
            and self.height == other.height
            and self.transform == other.transform
        )

    def copy(self) -> SfdPattern:
        return copy(self)

    def deepcopy(self) -> SfdPattern:
        return deepcopy(self)


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
    fill_gradient: SfdGradient | None
    stroke_gradient: SfdGradient | None
    fill_pattern: SfdPattern | None
    stroke_pattern: SfdPattern | None

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
        fill_gradient: SfdGradient | None = None,
        stroke_gradient: SfdGradient | None = None,
        fill_pattern: SfdPattern | None = None,
        stroke_pattern: SfdPattern | None = None,
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
        self.fill_gradient = fill_gradient
        self.stroke_gradient = stroke_gradient
        self.fill_pattern = fill_pattern
        self.stroke_pattern = stroke_pattern

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
            self.fill_gradient,
            self.stroke_gradient,
            self.fill_pattern,
            self.stroke_pattern,
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
        result.fill_gradient = deepcopy(self.fill_gradient, memo)
        result.stroke_gradient = deepcopy(self.stroke_gradient, memo)
        result.fill_pattern = deepcopy(self.fill_pattern, memo)
        result.stroke_pattern = deepcopy(self.stroke_pattern, memo)
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
            and self.fill_gradient == other.fill_gradient
            and self.stroke_gradient == other.stroke_gradient
            and self.fill_pattern == other.fill_pattern
            and self.stroke_pattern == other.stroke_pattern
        )

    def copy(self) -> SfdPaint:
        return copy(self)

    def deepcopy(self) -> SfdPaint:
        return deepcopy(self)
