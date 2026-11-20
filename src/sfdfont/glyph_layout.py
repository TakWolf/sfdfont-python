from __future__ import annotations

from copy import copy, deepcopy
from typing import Any

from sfdfont.record import SfdRecord


class SfdPositionValue:
    x_offset: int
    y_offset: int
    x_advance: int
    y_advance: int
    x_adjustments: dict[int, int]
    y_adjustments: dict[int, int]
    x_advance_adjustments: dict[int, int]
    y_advance_adjustments: dict[int, int]

    def __init__(
        self,
        x_offset: int = 0,
        y_offset: int = 0,
        x_advance: int = 0,
        y_advance: int = 0,
        x_adjustments: dict[int, int] | None = None,
        y_adjustments: dict[int, int] | None = None,
        x_advance_adjustments: dict[int, int] | None = None,
        y_advance_adjustments: dict[int, int] | None = None,
    ) -> None:
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.x_advance = x_advance
        self.y_advance = y_advance
        self.x_adjustments = x_adjustments if x_adjustments is not None else {}
        self.y_adjustments = y_adjustments if y_adjustments is not None else {}
        self.x_advance_adjustments = x_advance_adjustments if x_advance_adjustments is not None else {}
        self.y_advance_adjustments = y_advance_adjustments if y_advance_adjustments is not None else {}

    def __copy__(self) -> SfdPositionValue:
        return SfdPositionValue(
            self.x_offset,
            self.y_offset,
            self.x_advance,
            self.y_advance,
            self.x_adjustments,
            self.y_adjustments,
            self.x_advance_adjustments,
            self.y_advance_adjustments,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdPositionValue:
        result = copy(self)
        memo[id(self)] = result
        result.x_offset = deepcopy(self.x_offset, memo)
        result.y_offset = deepcopy(self.y_offset, memo)
        result.x_advance = deepcopy(self.x_advance, memo)
        result.y_advance = deepcopy(self.y_advance, memo)
        result.x_adjustments = deepcopy(self.x_adjustments, memo)
        result.y_adjustments = deepcopy(self.y_adjustments, memo)
        result.x_advance_adjustments = deepcopy(self.x_advance_adjustments, memo)
        result.y_advance_adjustments = deepcopy(self.y_advance_adjustments, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdPositionValue):
            return NotImplemented
        return (
            self.x_offset == other.x_offset
            and self.y_offset == other.y_offset
            and self.x_advance == other.x_advance
            and self.y_advance == other.y_advance
            and self.x_adjustments == other.x_adjustments
            and self.y_adjustments == other.y_adjustments
            and self.x_advance_adjustments == other.x_advance_adjustments
            and self.y_advance_adjustments == other.y_advance_adjustments
        )

    def __repr__(self) -> str:
        return (
            f'SfdPositionValue('
            f'x_offset={self.x_offset!r}, '
            f'y_offset={self.y_offset!r}, '
            f'x_advance={self.x_advance!r}, '
            f'y_advance={self.y_advance!r}, '
            f'x_adjustments={self.x_adjustments!r}, '
            f'y_adjustments={self.y_adjustments!r}, '
            f'x_advance_adjustments={self.x_advance_adjustments!r}, '
            f'y_advance_adjustments={self.y_advance_adjustments!r}'
            f')'
        )

    def copy(self) -> SfdPositionValue:
        return copy(self)

    def deepcopy(self) -> SfdPositionValue:
        return deepcopy(self)


class SfdPosition:
    subtable: str
    value: SfdPositionValue

    def __init__(
        self,
        subtable: str = '',
        value: SfdPositionValue | None = None,
    ) -> None:
        self.subtable = subtable
        self.value = value if value is not None else SfdPositionValue()

    def __copy__(self) -> SfdPosition:
        return SfdPosition(
            self.subtable,
            self.value,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdPosition:
        result = copy(self)
        memo[id(self)] = result
        result.subtable = deepcopy(self.subtable, memo)
        result.value = deepcopy(self.value, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdPosition):
            return NotImplemented
        return self.subtable == other.subtable and self.value == other.value

    def __repr__(self) -> str:
        return f'SfdPosition(subtable={self.subtable!r}, value={self.value!r})'

    def copy(self) -> SfdPosition:
        return copy(self)

    def deepcopy(self) -> SfdPosition:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdPosition:
        from sfdfont._glyph_layout import decode_position

        return decode_position(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._glyph_layout import encode_position

        return encode_position(self)


class SfdPairPosition:
    subtable: str
    glyph: str
    first: SfdPositionValue
    second: SfdPositionValue

    def __init__(
        self,
        subtable: str = '',
        glyph: str = '.notdef',
        first: SfdPositionValue | None = None,
        second: SfdPositionValue | None = None,
    ) -> None:
        self.subtable = subtable
        self.glyph = glyph
        self.first = first if first is not None else SfdPositionValue()
        self.second = second if second is not None else SfdPositionValue()

    def __copy__(self) -> SfdPairPosition:
        return SfdPairPosition(
            self.subtable,
            self.glyph,
            self.first,
            self.second,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdPairPosition:
        result = copy(self)
        memo[id(self)] = result
        result.subtable = deepcopy(self.subtable, memo)
        result.glyph = deepcopy(self.glyph, memo)
        result.first = deepcopy(self.first, memo)
        result.second = deepcopy(self.second, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdPairPosition):
            return NotImplemented
        return (
            self.subtable == other.subtable
            and self.glyph == other.glyph
            and self.first == other.first
            and self.second == other.second
        )

    def __repr__(self) -> str:
        return (
            f'SfdPairPosition('
            f'subtable={self.subtable!r}, '
            f'glyph={self.glyph!r}, '
            f'first={self.first!r}, '
            f'second={self.second!r}'
            f')'
        )

    def copy(self) -> SfdPairPosition:
        return copy(self)

    def deepcopy(self) -> SfdPairPosition:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdPairPosition:
        from sfdfont._glyph_layout import decode_pair

        return decode_pair(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._glyph_layout import encode_pair

        return encode_pair(self)


class SfdSubstitution:
    keyword: str
    subtable: str
    glyphs: list[str]

    def __init__(
        self,
        keyword: str = 'Substitution2:',
        subtable: str = '',
        glyphs: list[str] | None = None,
    ) -> None:
        self.keyword = keyword
        self.subtable = subtable
        self.glyphs = glyphs if glyphs is not None else []

    def __copy__(self) -> SfdSubstitution:
        return SfdSubstitution(
            self.keyword,
            self.subtable,
            self.glyphs,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdSubstitution:
        result = copy(self)
        memo[id(self)] = result
        result.keyword = deepcopy(self.keyword, memo)
        result.subtable = deepcopy(self.subtable, memo)
        result.glyphs = deepcopy(self.glyphs, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdSubstitution):
            return NotImplemented
        return self.keyword == other.keyword and self.subtable == other.subtable and self.glyphs == other.glyphs

    def __repr__(self) -> str:
        return f'SfdSubstitution(keyword={self.keyword!r}, subtable={self.subtable!r}, glyphs={self.glyphs!r})'

    def copy(self) -> SfdSubstitution:
        return copy(self)

    def deepcopy(self) -> SfdSubstitution:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdSubstitution:
        from sfdfont._glyph_layout import decode_substitution

        return decode_substitution(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._glyph_layout import encode_substitution

        return encode_substitution(self)


class SfdLigatureCarets:
    carets: list[int]

    def __init__(
        self,
        carets: list[int] | None = None,
    ) -> None:
        self.carets = carets if carets is not None else []

    def __copy__(self) -> SfdLigatureCarets:
        return SfdLigatureCarets(
            self.carets,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdLigatureCarets:
        result = copy(self)
        memo[id(self)] = result
        result.carets = deepcopy(self.carets, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdLigatureCarets):
            return NotImplemented
        return self.carets == other.carets

    def __repr__(self) -> str:
        return f'SfdLigatureCarets(carets={self.carets!r})'

    def copy(self) -> SfdLigatureCarets:
        return copy(self)

    def deepcopy(self) -> SfdLigatureCarets:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdLigatureCarets:
        from sfdfont._glyph_layout import decode_carets

        return decode_carets(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._glyph_layout import encode_carets

        return encode_carets(self)


class SfdAnchor:
    name: str
    x: float
    y: float
    kind: str
    ligature_index: int
    x_adjustments: dict[int, int]
    y_adjustments: dict[int, int]
    ttf_index: int | None

    def __init__(
        self,
        name: str = '',
        x: float = 0,
        y: float = 0,
        kind: str = 'basechar',
        ligature_index: int = 0,
        x_adjustments: dict[int, int] | None = None,
        y_adjustments: dict[int, int] | None = None,
        ttf_index: int | None = None,
    ) -> None:
        self.name = name
        self.x = x
        self.y = y
        self.kind = kind
        self.ligature_index = ligature_index
        self.x_adjustments = x_adjustments if x_adjustments is not None else {}
        self.y_adjustments = y_adjustments if y_adjustments is not None else {}
        self.ttf_index = ttf_index

    def __copy__(self) -> SfdAnchor:
        return SfdAnchor(
            self.name,
            self.x,
            self.y,
            self.kind,
            self.ligature_index,
            self.x_adjustments,
            self.y_adjustments,
            self.ttf_index,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdAnchor:
        result = copy(self)
        memo[id(self)] = result
        result.name = deepcopy(self.name, memo)
        result.x = deepcopy(self.x, memo)
        result.y = deepcopy(self.y, memo)
        result.kind = deepcopy(self.kind, memo)
        result.ligature_index = deepcopy(self.ligature_index, memo)
        result.x_adjustments = deepcopy(self.x_adjustments, memo)
        result.y_adjustments = deepcopy(self.y_adjustments, memo)
        result.ttf_index = deepcopy(self.ttf_index, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdAnchor):
            return NotImplemented
        return (
            self.name == other.name
            and self.x == other.x
            and self.y == other.y
            and self.kind == other.kind
            and self.ligature_index == other.ligature_index
            and self.x_adjustments == other.x_adjustments
            and self.y_adjustments == other.y_adjustments
            and self.ttf_index == other.ttf_index
        )

    def __repr__(self) -> str:
        return (
            f'SfdAnchor('
            f'name={self.name!r}, '
            f'x={self.x!r}, '
            f'y={self.y!r}, '
            f'kind={self.kind!r}, '
            f'ligature_index={self.ligature_index!r}, '
            f'x_adjustments={self.x_adjustments!r}, '
            f'y_adjustments={self.y_adjustments!r}, '
            f'ttf_index={self.ttf_index!r}'
            f')'
        )

    def copy(self) -> SfdAnchor:
        return copy(self)

    def deepcopy(self) -> SfdAnchor:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdAnchor:
        from sfdfont._glyph_layout import decode_anchor

        return decode_anchor(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._glyph_layout import encode_anchor

        return encode_anchor(self)


class SfdAnchorClass:
    name: str
    subtable: str | None
    kind: int | None

    def __init__(
        self,
        name: str = '',
        subtable: str | None = None,
        kind: int | None = None,
    ) -> None:
        self.name = name
        self.subtable = subtable
        self.kind = kind

    def __copy__(self) -> SfdAnchorClass:
        return SfdAnchorClass(
            self.name,
            self.subtable,
            self.kind,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdAnchorClass:
        result = copy(self)
        memo[id(self)] = result
        result.name = deepcopy(self.name, memo)
        result.subtable = deepcopy(self.subtable, memo)
        result.kind = deepcopy(self.kind, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdAnchorClass):
            return NotImplemented
        return self.name == other.name and self.subtable == other.subtable and self.kind == other.kind

    def __repr__(self) -> str:
        return f'SfdAnchorClass(name={self.name!r}, subtable={self.subtable!r}, kind={self.kind!r})'

    def copy(self) -> SfdAnchorClass:
        return copy(self)

    def deepcopy(self) -> SfdAnchorClass:
        return deepcopy(self)


class SfdAnchorClasses:
    classes: list[SfdAnchorClass]

    def __init__(
        self,
        classes: list[SfdAnchorClass] | None = None,
    ) -> None:
        self.classes = classes if classes is not None else []

    def __copy__(self) -> SfdAnchorClasses:
        return SfdAnchorClasses(
            self.classes,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdAnchorClasses:
        result = copy(self)
        memo[id(self)] = result
        result.classes = deepcopy(self.classes, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdAnchorClasses):
            return NotImplemented
        return self.classes == other.classes

    def __repr__(self) -> str:
        return f'SfdAnchorClasses(classes={self.classes!r})'

    def copy(self) -> SfdAnchorClasses:
        return copy(self)

    def deepcopy(self) -> SfdAnchorClasses:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdAnchorClasses:
        from sfdfont._glyph_layout import decode_anchor_classes

        return decode_anchor_classes(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._glyph_layout import encode_anchor_classes

        return encode_anchor_classes(self)


class SfdKerningPair:
    target: int
    offset: int
    subtable: str
    adjustments: dict[int, int]

    def __init__(
        self,
        target: int = 0,
        offset: int = 0,
        subtable: str = '',
        adjustments: dict[int, int] | None = None,
    ) -> None:
        self.target = target
        self.offset = offset
        self.subtable = subtable
        self.adjustments = adjustments if adjustments is not None else {}

    def __copy__(self) -> SfdKerningPair:
        return SfdKerningPair(
            self.target,
            self.offset,
            self.subtable,
            self.adjustments,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdKerningPair:
        result = copy(self)
        memo[id(self)] = result
        result.target = deepcopy(self.target, memo)
        result.offset = deepcopy(self.offset, memo)
        result.subtable = deepcopy(self.subtable, memo)
        result.adjustments = deepcopy(self.adjustments, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdKerningPair):
            return NotImplemented
        return (
            self.target == other.target
            and self.offset == other.offset
            and self.subtable == other.subtable
            and self.adjustments == other.adjustments
        )

    def __repr__(self) -> str:
        return (
            f'SfdKerningPair('
            f'target={self.target!r}, '
            f'offset={self.offset!r}, '
            f'subtable={self.subtable!r}, '
            f'adjustments={self.adjustments!r}'
            f')'
        )

    def copy(self) -> SfdKerningPair:
        return copy(self)

    def deepcopy(self) -> SfdKerningPair:
        return deepcopy(self)


class SfdKerningPairs:
    keyword: str
    pairs: list[SfdKerningPair]

    def __init__(
        self,
        keyword: str = 'Kerns2:',
        pairs: list[SfdKerningPair] | None = None,
    ) -> None:
        self.keyword = keyword
        self.pairs = pairs if pairs is not None else []

    def __copy__(self) -> SfdKerningPairs:
        return SfdKerningPairs(
            self.keyword,
            self.pairs,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdKerningPairs:
        result = copy(self)
        memo[id(self)] = result
        result.keyword = deepcopy(self.keyword, memo)
        result.pairs = deepcopy(self.pairs, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdKerningPairs):
            return NotImplemented
        return self.keyword == other.keyword and self.pairs == other.pairs

    def __repr__(self) -> str:
        return f'SfdKerningPairs(keyword={self.keyword!r}, pairs={self.pairs!r})'

    def copy(self) -> SfdKerningPairs:
        return copy(self)

    def deepcopy(self) -> SfdKerningPairs:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdKerningPairs:
        from sfdfont._glyph_layout import decode_kerning_pairs

        return decode_kerning_pairs(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._glyph_layout import encode_kerning_pairs

        return encode_kerning_pairs(self)
