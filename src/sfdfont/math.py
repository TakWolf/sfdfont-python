from __future__ import annotations

from copy import copy, deepcopy
from typing import Any

from sfdfont.record import SfdRecord


class SfdMathValue:
    keyword: str
    value: int
    adjustments: dict[int, int]

    def __init__(
        self,
        keyword: str = 'ItalicCorrection:',
        value: int = 0,
        adjustments: dict[int, int] | None = None,
    ) -> None:
        self.keyword = keyword
        self.value = value
        self.adjustments = adjustments if adjustments is not None else {}

    def __copy__(self) -> SfdMathValue:
        return SfdMathValue(
            self.keyword,
            self.value,
            self.adjustments,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdMathValue:
        result = copy(self)
        memo[id(self)] = result
        result.keyword = deepcopy(self.keyword, memo)
        result.value = deepcopy(self.value, memo)
        result.adjustments = deepcopy(self.adjustments, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdMathValue):
            return NotImplemented
        return self.keyword == other.keyword and self.value == other.value and self.adjustments == other.adjustments

    def __repr__(self) -> str:
        return f'SfdMathValue(keyword={self.keyword!r}, value={self.value!r}, adjustments={self.adjustments!r})'

    def copy(self) -> SfdMathValue:
        return copy(self)

    def deepcopy(self) -> SfdMathValue:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdMathValue:
        from sfdfont._math import decode_math_value

        return decode_math_value(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._math import encode_math_value

        return encode_math_value(self)


class SfdGlyphPart:
    glyph: str
    is_extender: bool
    start_connector: int
    end_connector: int
    full_advance: int

    def __init__(
        self,
        glyph: str = '.notdef',
        is_extender: bool = False,
        start_connector: int = 0,
        end_connector: int = 0,
        full_advance: int = 0,
    ) -> None:
        self.glyph = glyph
        self.is_extender = is_extender
        self.start_connector = start_connector
        self.end_connector = end_connector
        self.full_advance = full_advance

    def __copy__(self) -> SfdGlyphPart:
        return SfdGlyphPart(
            self.glyph,
            self.is_extender,
            self.start_connector,
            self.end_connector,
            self.full_advance,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdGlyphPart:
        result = copy(self)
        memo[id(self)] = result
        result.glyph = deepcopy(self.glyph, memo)
        result.is_extender = deepcopy(self.is_extender, memo)
        result.start_connector = deepcopy(self.start_connector, memo)
        result.end_connector = deepcopy(self.end_connector, memo)
        result.full_advance = deepcopy(self.full_advance, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdGlyphPart):
            return NotImplemented
        return (
            self.glyph == other.glyph
            and self.is_extender == other.is_extender
            and self.start_connector == other.start_connector
            and self.end_connector == other.end_connector
            and self.full_advance == other.full_advance
        )

    def __repr__(self) -> str:
        return (
            f'SfdGlyphPart('
            f'glyph={self.glyph!r}, '
            f'is_extender={self.is_extender!r}, '
            f'start_connector={self.start_connector!r}, '
            f'end_connector={self.end_connector!r}, '
            f'full_advance={self.full_advance!r}'
            f')'
        )

    def copy(self) -> SfdGlyphPart:
        return copy(self)

    def deepcopy(self) -> SfdGlyphPart:
        return deepcopy(self)


class SfdGlyphAssembly:
    keyword: str
    parts: list[SfdGlyphPart]

    def __init__(
        self,
        keyword: str = 'GlyphCompositionVertical:',
        parts: list[SfdGlyphPart] | None = None,
    ) -> None:
        self.keyword = keyword
        self.parts = parts if parts is not None else []

    def __copy__(self) -> SfdGlyphAssembly:
        return SfdGlyphAssembly(
            self.keyword,
            self.parts,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdGlyphAssembly:
        result = copy(self)
        memo[id(self)] = result
        result.keyword = deepcopy(self.keyword, memo)
        result.parts = deepcopy(self.parts, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdGlyphAssembly):
            return NotImplemented
        return self.keyword == other.keyword and self.parts == other.parts

    def __repr__(self) -> str:
        return f'SfdGlyphAssembly(keyword={self.keyword!r}, parts={self.parts!r})'

    def copy(self) -> SfdGlyphAssembly:
        return copy(self)

    def deepcopy(self) -> SfdGlyphAssembly:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdGlyphAssembly:
        from sfdfont._math import decode_assembly

        return decode_assembly(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._math import encode_assembly

        return encode_assembly(self)


class SfdGlyphVariants:
    keyword: str
    glyphs: list[str]

    def __init__(
        self,
        keyword: str = 'GlyphVariantsVertical:',
        glyphs: list[str] | None = None,
    ) -> None:
        self.keyword = keyword
        self.glyphs = glyphs if glyphs is not None else []

    def __copy__(self) -> SfdGlyphVariants:
        return SfdGlyphVariants(
            self.keyword,
            self.glyphs,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdGlyphVariants:
        result = copy(self)
        memo[id(self)] = result
        result.keyword = deepcopy(self.keyword, memo)
        result.glyphs = deepcopy(self.glyphs, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdGlyphVariants):
            return NotImplemented
        return self.keyword == other.keyword and self.glyphs == other.glyphs

    def __repr__(self) -> str:
        return f'SfdGlyphVariants(keyword={self.keyword!r}, glyphs={self.glyphs!r})'

    def copy(self) -> SfdGlyphVariants:
        return copy(self)

    def deepcopy(self) -> SfdGlyphVariants:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdGlyphVariants:
        from sfdfont._math import decode_variants

        return decode_variants(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._math import encode_variants

        return encode_variants(self)


class SfdMathKernEntry:
    height: int
    kern: int
    height_adjustments: dict[int, int]
    kern_adjustments: dict[int, int]

    def __init__(
        self,
        height: int = 0,
        kern: int = 0,
        height_adjustments: dict[int, int] | None = None,
        kern_adjustments: dict[int, int] | None = None,
    ) -> None:
        self.height = height
        self.kern = kern
        self.height_adjustments = height_adjustments if height_adjustments is not None else {}
        self.kern_adjustments = kern_adjustments if kern_adjustments is not None else {}

    def __copy__(self) -> SfdMathKernEntry:
        return SfdMathKernEntry(
            self.height,
            self.kern,
            self.height_adjustments,
            self.kern_adjustments,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdMathKernEntry:
        result = copy(self)
        memo[id(self)] = result
        result.height = deepcopy(self.height, memo)
        result.kern = deepcopy(self.kern, memo)
        result.height_adjustments = deepcopy(self.height_adjustments, memo)
        result.kern_adjustments = deepcopy(self.kern_adjustments, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdMathKernEntry):
            return NotImplemented
        return (
            self.height == other.height
            and self.kern == other.kern
            and self.height_adjustments == other.height_adjustments
            and self.kern_adjustments == other.kern_adjustments
        )

    def __repr__(self) -> str:
        return (
            f'SfdMathKernEntry('
            f'height={self.height!r}, '
            f'kern={self.kern!r}, '
            f'height_adjustments={self.height_adjustments!r}, '
            f'kern_adjustments={self.kern_adjustments!r}'
            f')'
        )

    def copy(self) -> SfdMathKernEntry:
        return copy(self)

    def deepcopy(self) -> SfdMathKernEntry:
        return deepcopy(self)


class SfdMathKern:
    keyword: str
    entries: list[SfdMathKernEntry]

    def __init__(
        self,
        keyword: str = 'TopRightVertex:',
        entries: list[SfdMathKernEntry] | None = None,
    ) -> None:
        self.keyword = keyword
        self.entries = entries if entries is not None else []

    def __copy__(self) -> SfdMathKern:
        return SfdMathKern(
            self.keyword,
            self.entries,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdMathKern:
        result = copy(self)
        memo[id(self)] = result
        result.keyword = deepcopy(self.keyword, memo)
        result.entries = deepcopy(self.entries, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdMathKern):
            return NotImplemented
        return self.keyword == other.keyword and self.entries == other.entries

    def __repr__(self) -> str:
        return f'SfdMathKern(keyword={self.keyword!r}, entries={self.entries!r})'

    def copy(self) -> SfdMathKern:
        return copy(self)

    def deepcopy(self) -> SfdMathKern:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdMathKern:
        from sfdfont._math import decode_math_kern

        return decode_math_kern(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._math import encode_math_kern

        return encode_math_kern(self)
