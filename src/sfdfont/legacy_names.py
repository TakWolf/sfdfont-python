from __future__ import annotations

from copy import copy, deepcopy
from typing import Any

from sfdfont.record import SfdRecord


class SfdStyleMapName:
    keyword: str
    name: str
    quoted: bool

    def __init__(
        self,
        keyword: str = 'OS2StyleName:',
        name: str = 'regular',
        quoted: bool = True,
    ) -> None:
        self.keyword = keyword
        self.name = name
        self.quoted = quoted

    def __copy__(self) -> SfdStyleMapName:
        return SfdStyleMapName(
            self.keyword,
            self.name,
            self.quoted,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdStyleMapName:
        result = copy(self)
        memo[id(self)] = result
        result.keyword = deepcopy(self.keyword, memo)
        result.name = deepcopy(self.name, memo)
        result.quoted = deepcopy(self.quoted, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdStyleMapName):
            return NotImplemented
        return self.keyword == other.keyword and self.name == other.name and self.quoted == other.quoted

    def __repr__(self) -> str:
        return f'SfdStyleMapName(keyword={self.keyword!r}, name={self.name!r}, quoted={self.quoted!r})'

    def copy(self) -> SfdStyleMapName:
        return copy(self)

    def deepcopy(self) -> SfdStyleMapName:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdStyleMapName:
        from sfdfont._legacy_names import decode_style_map_name

        return decode_style_map_name(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._legacy_names import encode_style_map_name

        return encode_style_map_name(self)
