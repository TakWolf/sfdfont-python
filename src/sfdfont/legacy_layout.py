from __future__ import annotations

from copy import copy, deepcopy
from typing import Any

from sfdfont.glyph_layout import SfdPositionValue
from sfdfont.record import SfdRecord


class SfdLegacyBinding:
    flags: int | None
    script_language_index: int | None
    tag: str | tuple[int, int] | None

    def __init__(
        self,
        flags: int | None = None,
        script_language_index: int | None = None,
        tag: str | tuple[int, int] | None = None,
    ) -> None:
        self.flags = flags
        self.script_language_index = script_language_index
        self.tag = tag

    def __copy__(self) -> SfdLegacyBinding:
        return SfdLegacyBinding(
            self.flags,
            self.script_language_index,
            self.tag,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdLegacyBinding:
        result = copy(self)
        memo[id(self)] = result
        result.flags = deepcopy(self.flags, memo)
        result.script_language_index = deepcopy(self.script_language_index, memo)
        result.tag = deepcopy(self.tag, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdLegacyBinding):
            return NotImplemented
        return (
            self.flags == other.flags
            and self.script_language_index == other.script_language_index
            and self.tag == other.tag
        )

    def __repr__(self) -> str:
        return (
            f'SfdLegacyBinding('
            f'flags={self.flags!r}, '
            f'script_language_index={self.script_language_index!r}, '
            f'tag={self.tag!r}'
            f')'
        )

    def copy(self) -> SfdLegacyBinding:
        return copy(self)

    def deepcopy(self) -> SfdLegacyBinding:
        return deepcopy(self)


class SfdLegacyPst:
    keyword: str
    binding: SfdLegacyBinding
    glyphs: list[str]
    positions: list[SfdPositionValue]
    carets: list[int]
    pair_separator: bool

    def __init__(
        self,
        keyword: str = 'Ligature:',
        binding: SfdLegacyBinding | None = None,
        glyphs: list[str] | None = None,
        positions: list[SfdPositionValue] | None = None,
        carets: list[int] | None = None,
        pair_separator: bool = False,
    ) -> None:
        self.keyword = keyword
        self.binding = binding if binding is not None else SfdLegacyBinding()
        self.glyphs = glyphs if glyphs is not None else []
        self.positions = positions if positions is not None else []
        self.carets = carets if carets is not None else []
        self.pair_separator = pair_separator

    def __copy__(self) -> SfdLegacyPst:
        return SfdLegacyPst(
            self.keyword,
            self.binding,
            self.glyphs,
            self.positions,
            self.carets,
            self.pair_separator,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdLegacyPst:
        result = copy(self)
        memo[id(self)] = result
        result.keyword = deepcopy(self.keyword, memo)
        result.binding = deepcopy(self.binding, memo)
        result.glyphs = deepcopy(self.glyphs, memo)
        result.positions = deepcopy(self.positions, memo)
        result.carets = deepcopy(self.carets, memo)
        result.pair_separator = deepcopy(self.pair_separator, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdLegacyPst):
            return NotImplemented
        return (
            self.keyword == other.keyword
            and self.binding == other.binding
            and self.glyphs == other.glyphs
            and self.positions == other.positions
            and self.carets == other.carets
            and self.pair_separator == other.pair_separator
        )

    def __repr__(self) -> str:
        return (
            f'SfdLegacyPst('
            f'keyword={self.keyword!r}, '
            f'binding={self.binding!r}, '
            f'glyphs={self.glyphs!r}, '
            f'positions={self.positions!r}, '
            f'carets={self.carets!r}, '
            f'pair_separator={self.pair_separator!r}'
            f')'
        )

    def copy(self) -> SfdLegacyPst:
        return copy(self)

    def deepcopy(self) -> SfdLegacyPst:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdLegacyPst:
        from sfdfont._legacy_layout import decode_pst

        return decode_pst(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._legacy_layout import encode_pst

        return encode_pst(self)


class SfdLegacyKerningPair:
    target: int
    offset: int
    script_language_index: int | None
    flags: int | None
    adjustments: dict[int, int]

    def __init__(
        self,
        target: int = 0,
        offset: int = 0,
        script_language_index: int | None = None,
        flags: int | None = None,
        adjustments: dict[int, int] | None = None,
    ) -> None:
        self.target = target
        self.offset = offset
        self.script_language_index = script_language_index
        self.flags = flags
        self.adjustments = adjustments if adjustments is not None else {}

    def __copy__(self) -> SfdLegacyKerningPair:
        return SfdLegacyKerningPair(
            self.target,
            self.offset,
            self.script_language_index,
            self.flags,
            self.adjustments,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdLegacyKerningPair:
        result = copy(self)
        memo[id(self)] = result
        result.target = deepcopy(self.target, memo)
        result.offset = deepcopy(self.offset, memo)
        result.script_language_index = deepcopy(self.script_language_index, memo)
        result.flags = deepcopy(self.flags, memo)
        result.adjustments = deepcopy(self.adjustments, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdLegacyKerningPair):
            return NotImplemented
        return (
            self.target == other.target
            and self.offset == other.offset
            and self.script_language_index == other.script_language_index
            and self.flags == other.flags
            and self.adjustments == other.adjustments
        )

    def __repr__(self) -> str:
        return (
            f'SfdLegacyKerningPair('
            f'target={self.target!r}, '
            f'offset={self.offset!r}, '
            f'script_language_index={self.script_language_index!r}, '
            f'flags={self.flags!r}, '
            f'adjustments={self.adjustments!r}'
            f')'
        )

    def copy(self) -> SfdLegacyKerningPair:
        return copy(self)

    def deepcopy(self) -> SfdLegacyKerningPair:
        return deepcopy(self)


class SfdLegacyKerningPairs:
    keyword: str
    pairs: list[SfdLegacyKerningPair]

    def __init__(
        self,
        keyword: str = 'Kerns:',
        pairs: list[SfdLegacyKerningPair] | None = None,
    ) -> None:
        self.keyword = keyword
        self.pairs = pairs if pairs is not None else []

    def __copy__(self) -> SfdLegacyKerningPairs:
        return SfdLegacyKerningPairs(
            self.keyword,
            self.pairs,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdLegacyKerningPairs:
        result = copy(self)
        memo[id(self)] = result
        result.keyword = deepcopy(self.keyword, memo)
        result.pairs = deepcopy(self.pairs, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdLegacyKerningPairs):
            return NotImplemented
        return self.keyword == other.keyword and self.pairs == other.pairs

    def __repr__(self) -> str:
        return f'SfdLegacyKerningPairs(keyword={self.keyword!r}, pairs={self.pairs!r})'

    def copy(self) -> SfdLegacyKerningPairs:
        return copy(self)

    def deepcopy(self) -> SfdLegacyKerningPairs:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdLegacyKerningPairs:
        from sfdfont._legacy_layout import decode_pairs

        return decode_pairs(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._legacy_layout import encode_pairs

        return encode_pairs(self)


class SfdLegacyAnchorClass:
    name: str
    feature_tag: str
    flags: int | None
    script_language_index: int | None
    merge_with: int | None
    kind: int | None

    def __init__(
        self,
        name: str = '',
        feature_tag: str = 'mark',
        flags: int | None = None,
        script_language_index: int | None = None,
        merge_with: int | None = None,
        kind: int | None = None,
    ) -> None:
        self.name = name
        self.feature_tag = feature_tag
        self.flags = flags
        self.script_language_index = script_language_index
        self.merge_with = merge_with
        self.kind = kind

    def __copy__(self) -> SfdLegacyAnchorClass:
        return SfdLegacyAnchorClass(
            self.name,
            self.feature_tag,
            self.flags,
            self.script_language_index,
            self.merge_with,
            self.kind,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdLegacyAnchorClass:
        result = copy(self)
        memo[id(self)] = result
        result.name = deepcopy(self.name, memo)
        result.feature_tag = deepcopy(self.feature_tag, memo)
        result.flags = deepcopy(self.flags, memo)
        result.script_language_index = deepcopy(self.script_language_index, memo)
        result.merge_with = deepcopy(self.merge_with, memo)
        result.kind = deepcopy(self.kind, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdLegacyAnchorClass):
            return NotImplemented
        return (
            self.name == other.name
            and self.feature_tag == other.feature_tag
            and self.flags == other.flags
            and self.script_language_index == other.script_language_index
            and self.merge_with == other.merge_with
            and self.kind == other.kind
        )

    def __repr__(self) -> str:
        return (
            f'SfdLegacyAnchorClass('
            f'name={self.name!r}, '
            f'feature_tag={self.feature_tag!r}, '
            f'flags={self.flags!r}, '
            f'script_language_index={self.script_language_index!r}, '
            f'merge_with={self.merge_with!r}, '
            f'kind={self.kind!r}'
            f')'
        )

    def copy(self) -> SfdLegacyAnchorClass:
        return copy(self)

    def deepcopy(self) -> SfdLegacyAnchorClass:
        return deepcopy(self)


class SfdLegacyAnchorClasses:
    classes: list[SfdLegacyAnchorClass]

    def __init__(
        self,
        classes: list[SfdLegacyAnchorClass] | None = None,
    ) -> None:
        self.classes = classes if classes is not None else []

    def __copy__(self) -> SfdLegacyAnchorClasses:
        return SfdLegacyAnchorClasses(
            self.classes,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdLegacyAnchorClasses:
        result = copy(self)
        memo[id(self)] = result
        result.classes = deepcopy(self.classes, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdLegacyAnchorClasses):
            return NotImplemented
        return self.classes == other.classes

    def __repr__(self) -> str:
        return f'SfdLegacyAnchorClasses(classes={self.classes!r})'

    def copy(self) -> SfdLegacyAnchorClasses:
        return copy(self)

    def deepcopy(self) -> SfdLegacyAnchorClasses:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdLegacyAnchorClasses:
        from sfdfont._legacy_layout import decode_anchor_classes

        return decode_anchor_classes(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._legacy_layout import encode_anchor_classes

        return encode_anchor_classes(self)
