from __future__ import annotations

from copy import copy, deepcopy
from typing import Any

from sfdfont.record import SfdRecord


class SfdFontMetric:
    keyword: str
    value: int

    def __init__(
        self,
        keyword: str = 'OS2TypoAscent:',
        value: int = 0,
    ) -> None:
        self.keyword = keyword
        self.value = value

    def __copy__(self) -> SfdFontMetric:
        return SfdFontMetric(
            self.keyword,
            self.value,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdFontMetric:
        result = copy(self)
        memo[id(self)] = result
        result.keyword = deepcopy(self.keyword, memo)
        result.value = deepcopy(self.value, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdFontMetric):
            return NotImplemented
        return self.keyword == other.keyword and self.value == other.value

    def __repr__(self) -> str:
        return f'SfdFontMetric(keyword={self.keyword!r}, value={self.value!r})'

    def copy(self) -> SfdFontMetric:
        return copy(self)

    def deepcopy(self) -> SfdFontMetric:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdFontMetric:
        from sfdfont._metrics import decode_metric

        return decode_metric(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._metrics import encode_metric

        return encode_metric(self)


class SfdFontRealMetric:
    keyword: str
    value: float

    def __init__(
        self,
        keyword: str = 'ItalicAngle:',
        value: float = 0,
    ) -> None:
        self.keyword = keyword
        self.value = value

    def __copy__(self) -> SfdFontRealMetric:
        return SfdFontRealMetric(
            self.keyword,
            self.value,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdFontRealMetric:
        result = copy(self)
        memo[id(self)] = result
        result.keyword = deepcopy(self.keyword, memo)
        result.value = deepcopy(self.value, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdFontRealMetric):
            return NotImplemented
        return self.keyword == other.keyword and self.value == other.value

    def __repr__(self) -> str:
        return f'SfdFontRealMetric(keyword={self.keyword!r}, value={self.value!r})'

    def copy(self) -> SfdFontRealMetric:
        return copy(self)

    def deepcopy(self) -> SfdFontRealMetric:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdFontRealMetric:
        from sfdfont._metrics import decode_real_metric

        return decode_real_metric(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._metrics import encode_real_metric

        return encode_real_metric(self)
