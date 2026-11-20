from __future__ import annotations

from copy import copy, deepcopy
from typing import Any

from sfdfont.record import SfdRecord


class SfdGlyphGroup:
    name: str
    glyphs: list[str]

    def __init__(
        self,
        name: str = '',
        glyphs: list[str] | None = None,
    ) -> None:
        self.name = name
        self.glyphs = glyphs if glyphs is not None else []

    def __copy__(self) -> SfdGlyphGroup:
        return SfdGlyphGroup(
            self.name,
            self.glyphs,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdGlyphGroup:
        result = copy(self)
        memo[id(self)] = result
        result.name = deepcopy(self.name, memo)
        result.glyphs = deepcopy(self.glyphs, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdGlyphGroup):
            return NotImplemented
        return self.name == other.name and self.glyphs == other.glyphs

    def __repr__(self) -> str:
        return f'SfdGlyphGroup(name={self.name!r}, glyphs={self.glyphs!r})'

    def copy(self) -> SfdGlyphGroup:
        return copy(self)

    def deepcopy(self) -> SfdGlyphGroup:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdGlyphGroup:
        from sfdfont._groups import decode_group

        return decode_group(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._groups import encode_group

        return encode_group(self)


class SfdGroupKerningPair:
    keyword: str
    left: str
    right: str
    offset: int

    def __init__(
        self,
        keyword: str = 'GroupKern:',
        left: str = '',
        right: str = '',
        offset: int = 0,
    ) -> None:
        self.keyword = keyword
        self.left = left
        self.right = right
        self.offset = offset

    def __copy__(self) -> SfdGroupKerningPair:
        return SfdGroupKerningPair(
            self.keyword,
            self.left,
            self.right,
            self.offset,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdGroupKerningPair:
        result = copy(self)
        memo[id(self)] = result
        result.keyword = deepcopy(self.keyword, memo)
        result.left = deepcopy(self.left, memo)
        result.right = deepcopy(self.right, memo)
        result.offset = deepcopy(self.offset, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdGroupKerningPair):
            return NotImplemented
        return (
            self.keyword == other.keyword
            and self.left == other.left
            and self.right == other.right
            and self.offset == other.offset
        )

    def __repr__(self) -> str:
        return (
            f'SfdGroupKerningPair('
            f'keyword={self.keyword!r}, '
            f'left={self.left!r}, '
            f'right={self.right!r}, '
            f'offset={self.offset!r}'
            f')'
        )

    def copy(self) -> SfdGroupKerningPair:
        return copy(self)

    def deepcopy(self) -> SfdGroupKerningPair:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdGroupKerningPair:
        from sfdfont._groups import decode_group_pair

        return decode_group_pair(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._groups import encode_group_pair

        return encode_group_pair(self)
