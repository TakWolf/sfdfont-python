from __future__ import annotations

from copy import copy, deepcopy
from typing import Any

from sfdfont.record import SfdRecord


class SfdFontText:
    """Plain font metadata, including uninterpreted XUID expressions."""

    keyword: str
    text: str

    def __init__(self, keyword: str = 'FONDName:', text: str = '') -> None:
        self.keyword = keyword
        self.text = text

    def __copy__(self) -> SfdFontText:
        return SfdFontText(self.keyword, self.text)

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdFontText:
        result = copy(self)
        memo[id(self)] = result
        result.keyword = deepcopy(self.keyword, memo)
        result.text = deepcopy(self.text, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdFontText):
            return NotImplemented
        return self.keyword == other.keyword and self.text == other.text

    def __repr__(self) -> str:
        return f'SfdFontText(keyword={self.keyword!r}, text={self.text!r})'

    def copy(self) -> SfdFontText:
        return copy(self)

    def deepcopy(self) -> SfdFontText:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdFontText:
        from sfdfont._font_text import decode_font_text

        return decode_font_text(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._font_text import encode_font_text

        return encode_font_text(self)
