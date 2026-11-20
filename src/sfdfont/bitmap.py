from __future__ import annotations

from copy import copy, deepcopy
from typing import Any


class SfdBitmapProperty:
    name: str
    type: int
    value: str | int

    def __init__(
        self,
        name: str,
        type: int,
        value: str | int,
    ) -> None:
        self.name = name
        self.type = type
        self.value = value

    def __copy__(self) -> SfdBitmapProperty:
        return SfdBitmapProperty(
            self.name,
            self.type,
            self.value,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdBitmapProperty:
        copied = copy(self)
        memo[id(self)] = copied
        copied.name = deepcopy(self.name, memo)
        copied.type = deepcopy(self.type, memo)
        copied.value = deepcopy(self.value, memo)
        return copied

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdBitmapProperty):
            return NotImplemented
        return self.name == other.name and self.type == other.type and self.value == other.value

    def __repr__(self) -> str:
        return f'SfdBitmapProperty(name={self.name!r}, type={self.type!r}, value={self.value!r})'

    def copy(self) -> SfdBitmapProperty:
        return copy(self)

    def deepcopy(self) -> SfdBitmapProperty:
        return deepcopy(self)


class SfdBitmapReference:
    source: int
    target: int
    x: int
    y: int
    selected: bool

    def __init__(
        self,
        source: int,
        target: int,
        x: int = 0,
        y: int = 0,
        selected: bool = False,
    ) -> None:
        self.source = source
        self.target = target
        self.x = x
        self.y = y
        self.selected = selected

    def __copy__(self) -> SfdBitmapReference:
        return SfdBitmapReference(
            self.source,
            self.target,
            self.x,
            self.y,
            self.selected,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdBitmapReference:
        copied = copy(self)
        memo[id(self)] = copied
        copied.source = deepcopy(self.source, memo)
        copied.target = deepcopy(self.target, memo)
        copied.x = deepcopy(self.x, memo)
        copied.y = deepcopy(self.y, memo)
        copied.selected = deepcopy(self.selected, memo)
        return copied

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdBitmapReference):
            return NotImplemented
        return (
            self.source == other.source
            and self.target == other.target
            and self.x == other.x
            and self.y == other.y
            and self.selected == other.selected
        )

    def __repr__(self) -> str:
        return (
            f'SfdBitmapReference('
            f'source={self.source!r}, '
            f'target={self.target!r}, '
            f'x={self.x!r}, '
            f'y={self.y!r}, '
            f'selected={self.selected!r}'
            f')'
        )

    def copy(self) -> SfdBitmapReference:
        return copy(self)

    def deepcopy(self) -> SfdBitmapReference:
        return deepcopy(self)


class SfdBitmapGlyph:
    """Rows run from ymax downwards; 1-bit rows use most-significant bit first.

    Grayscale strikes store one byte per pixel, in their native sample range.
    """

    glyph_id: int
    encoding: int
    advance: int
    xmin: int
    xmax: int
    ymin: int
    ymax: int
    data: bytes
    vertical_advance: int | None

    def __init__(
        self,
        glyph_id: int,
        encoding: int,
        advance: int,
        xmin: int,
        xmax: int,
        ymin: int,
        ymax: int,
        data: bytes,
        vertical_advance: int | None = None,
    ) -> None:
        self.glyph_id = glyph_id
        self.encoding = encoding
        self.advance = advance
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        self.data = data
        self.vertical_advance = vertical_advance

    def __copy__(self) -> SfdBitmapGlyph:
        return SfdBitmapGlyph(
            self.glyph_id,
            self.encoding,
            self.advance,
            self.xmin,
            self.xmax,
            self.ymin,
            self.ymax,
            self.data,
            self.vertical_advance,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdBitmapGlyph:
        copied = copy(self)
        memo[id(self)] = copied
        copied.glyph_id = deepcopy(self.glyph_id, memo)
        copied.encoding = deepcopy(self.encoding, memo)
        copied.advance = deepcopy(self.advance, memo)
        copied.xmin = deepcopy(self.xmin, memo)
        copied.xmax = deepcopy(self.xmax, memo)
        copied.ymin = deepcopy(self.ymin, memo)
        copied.ymax = deepcopy(self.ymax, memo)
        copied.data = deepcopy(self.data, memo)
        copied.vertical_advance = deepcopy(self.vertical_advance, memo)
        return copied

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdBitmapGlyph):
            return NotImplemented
        return (
            self.glyph_id == other.glyph_id
            and self.encoding == other.encoding
            and self.advance == other.advance
            and self.xmin == other.xmin
            and self.xmax == other.xmax
            and self.ymin == other.ymin
            and self.ymax == other.ymax
            and self.data == other.data
            and self.vertical_advance == other.vertical_advance
        )

    def __repr__(self) -> str:
        return (
            f'SfdBitmapGlyph('
            f'glyph_id={self.glyph_id!r}, '
            f'encoding={self.encoding!r}, '
            f'advance={self.advance!r}, '
            f'xmin={self.xmin!r}, '
            f'xmax={self.xmax!r}, '
            f'ymin={self.ymin!r}, '
            f'ymax={self.ymax!r}, '
            f'data={self.data!r}, '
            f'vertical_advance={self.vertical_advance!r}'
            f')'
        )

    @property
    def width(self) -> int:
        return self.xmax - self.xmin + 1

    @property
    def height(self) -> int:
        return self.ymax - self.ymin + 1

    def copy(self) -> SfdBitmapGlyph:
        return copy(self)

    def deepcopy(self) -> SfdBitmapGlyph:
        return deepcopy(self)


class SfdBitmapStrike:
    pixelsize: int
    ascent: int
    descent: int
    depth: int
    foundry: str | None
    resolution: int | None
    glyphs: list[SfdBitmapGlyph]
    references: list[SfdBitmapReference]
    properties: list[SfdBitmapProperty]

    def __init__(
        self,
        pixelsize: int,
        ascent: int,
        descent: int,
        depth: int = 1,
        foundry: str | None = None,
        resolution: int | None = None,
        glyphs: list[SfdBitmapGlyph] | None = None,
        references: list[SfdBitmapReference] | None = None,
        properties: list[SfdBitmapProperty] | None = None,
    ) -> None:
        self.pixelsize = pixelsize
        self.ascent = ascent
        self.descent = descent
        self.depth = depth
        self.foundry = foundry
        self.resolution = resolution
        self.glyphs = glyphs if glyphs is not None else []
        self.references = references if references is not None else []
        self.properties = properties if properties is not None else []

    def __copy__(self) -> SfdBitmapStrike:
        return SfdBitmapStrike(
            self.pixelsize,
            self.ascent,
            self.descent,
            self.depth,
            self.foundry,
            self.resolution,
            self.glyphs,
            self.references,
            self.properties,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdBitmapStrike:
        copied = copy(self)
        memo[id(self)] = copied
        copied.pixelsize = deepcopy(self.pixelsize, memo)
        copied.ascent = deepcopy(self.ascent, memo)
        copied.descent = deepcopy(self.descent, memo)
        copied.depth = deepcopy(self.depth, memo)
        copied.foundry = deepcopy(self.foundry, memo)
        copied.resolution = deepcopy(self.resolution, memo)
        copied.glyphs = deepcopy(self.glyphs, memo)
        copied.references = deepcopy(self.references, memo)
        copied.properties = deepcopy(self.properties, memo)
        return copied

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdBitmapStrike):
            return NotImplemented
        return (
            self.pixelsize == other.pixelsize
            and self.ascent == other.ascent
            and self.descent == other.descent
            and self.depth == other.depth
            and self.foundry == other.foundry
            and self.resolution == other.resolution
            and self.glyphs == other.glyphs
            and self.references == other.references
            and self.properties == other.properties
        )

    def __repr__(self) -> str:
        return (
            f'SfdBitmapStrike('
            f'pixelsize={self.pixelsize!r}, '
            f'ascent={self.ascent!r}, '
            f'descent={self.descent!r}, '
            f'depth={self.depth!r}, '
            f'foundry={self.foundry!r}, '
            f'resolution={self.resolution!r}, '
            f'glyphs={self.glyphs!r}, '
            f'references={self.references!r}, '
            f'properties={self.properties!r}'
            f')'
        )

    def pixels(self, glyph: SfdBitmapGlyph) -> list[list[int]]:
        stride = (glyph.width + 7) // 8 if self.depth == 1 else glyph.width
        if glyph.width <= 0 or glyph.height <= 0 or len(glyph.data) != stride * glyph.height:
            raise ValueError('bitmap dimensions do not match data')
        rows = []
        for y in range(glyph.height):
            row = glyph.data[y * stride : (y + 1) * stride]
            rows.append(
                [(row[x // 8] >> (7 - x % 8)) & 1 for x in range(glyph.width)] if self.depth == 1 else list(row)
            )
        return rows

    def copy(self) -> SfdBitmapStrike:
        return copy(self)

    def deepcopy(self) -> SfdBitmapStrike:
        return deepcopy(self)
