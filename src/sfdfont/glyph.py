from __future__ import annotations

from copy import copy, deepcopy
from typing import Any

from sfdfont.layer import SfdLayer
from sfdfont.payload import SfdPayload
from sfdfont.record import SfdRecord


class SfdAlternateUnicode:
    unicode: int
    variation_selector: int
    font_id: int

    def __init__(
        self,
        unicode: int,
        variation_selector: int = -1,
        font_id: int = 0,
    ) -> None:
        self.unicode = unicode
        self.variation_selector = variation_selector
        self.font_id = font_id

    def __copy__(self) -> SfdAlternateUnicode:
        return SfdAlternateUnicode(
            self.unicode,
            self.variation_selector,
            self.font_id,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdAlternateUnicode:
        copied = copy(self)
        memo[id(self)] = copied
        copied.unicode = deepcopy(self.unicode, memo)
        copied.variation_selector = deepcopy(self.variation_selector, memo)
        copied.font_id = deepcopy(self.font_id, memo)
        return copied

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdAlternateUnicode):
            return NotImplemented
        return (
            self.unicode == other.unicode
            and self.variation_selector == other.variation_selector
            and self.font_id == other.font_id
        )

    def __repr__(self) -> str:
        return (
            f'SfdAlternateUnicode('
            f'unicode={self.unicode!r}, '
            f'variation_selector={self.variation_selector!r}, '
            f'font_id={self.font_id!r}'
            f')'
        )

    def copy(self) -> SfdAlternateUnicode:
        return copy(self)

    def deepcopy(self) -> SfdAlternateUnicode:
        return deepcopy(self)


class SfdGlyph:
    name: str
    glyph_id: int
    encoding: int
    unicode: int
    width: int
    vertical_width: int | None
    alternate_unicodes: list[SfdAlternateUnicode]
    layers: list[SfdLayer]
    records: list[SfdRecord]
    payloads: list[SfdPayload]

    def __init__(
        self,
        name: str = '.notdef',
        glyph_id: int = 0,
        encoding: int = -1,
        unicode: int = -1,
        width: int = 1000,
        vertical_width: int | None = None,
        alternate_unicodes: list[SfdAlternateUnicode] | None = None,
        layers: list[SfdLayer] | None = None,
        records: list[SfdRecord] | None = None,
        payloads: list[SfdPayload] | None = None,
    ) -> None:
        self.name = name
        self.glyph_id = glyph_id
        self.encoding = encoding
        self.unicode = unicode
        self.width = width
        self.vertical_width = vertical_width
        self.alternate_unicodes = alternate_unicodes if alternate_unicodes is not None else []
        self.layers = layers if layers is not None else []
        self.records = records if records is not None else []
        self.payloads = payloads if payloads is not None else []

    def __copy__(self) -> SfdGlyph:
        return SfdGlyph(
            self.name,
            self.glyph_id,
            self.encoding,
            self.unicode,
            self.width,
            self.vertical_width,
            self.alternate_unicodes,
            self.layers,
            self.records,
            self.payloads,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdGlyph:
        copied = copy(self)
        memo[id(self)] = copied
        copied.name = deepcopy(self.name, memo)
        copied.glyph_id = deepcopy(self.glyph_id, memo)
        copied.encoding = deepcopy(self.encoding, memo)
        copied.unicode = deepcopy(self.unicode, memo)
        copied.width = deepcopy(self.width, memo)
        copied.vertical_width = deepcopy(self.vertical_width, memo)
        copied.alternate_unicodes = deepcopy(self.alternate_unicodes, memo)
        copied.layers = deepcopy(self.layers, memo)
        copied.records = deepcopy(self.records, memo)
        copied.payloads = deepcopy(self.payloads, memo)
        return copied

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdGlyph):
            return NotImplemented
        return (
            self.name == other.name
            and self.glyph_id == other.glyph_id
            and self.encoding == other.encoding
            and self.unicode == other.unicode
            and self.width == other.width
            and self.vertical_width == other.vertical_width
            and self.alternate_unicodes == other.alternate_unicodes
            and self.layers == other.layers
            and self.records == other.records
            and self.payloads == other.payloads
        )

    def __repr__(self) -> str:
        return (
            f'SfdGlyph('
            f'name={self.name!r}, '
            f'glyph_id={self.glyph_id!r}, '
            f'encoding={self.encoding!r}, '
            f'unicode={self.unicode!r}, '
            f'width={self.width!r}, '
            f'vertical_width={self.vertical_width!r}, '
            f'alternate_unicodes={self.alternate_unicodes!r}, '
            f'layers={self.layers!r}, '
            f'records={self.records!r}, '
            f'payloads={self.payloads!r}'
            f')'
        )

    def copy(self) -> SfdGlyph:
        return copy(self)

    def deepcopy(self) -> SfdGlyph:
        return deepcopy(self)
