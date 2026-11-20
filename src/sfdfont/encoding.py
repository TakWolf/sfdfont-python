from __future__ import annotations

from collections.abc import Iterable
from copy import copy, deepcopy
from typing import Any

from sfdfont.record import SfdRecord


class SfdEncodingRange:
    first: int
    last: int
    base: int

    def __init__(
        self,
        first: int = 0,
        last: int = 255,
        base: int = 0,
    ) -> None:
        self.first = first
        self.last = last
        self.base = base

    def __copy__(self) -> SfdEncodingRange:
        return SfdEncodingRange(
            self.first,
            self.last,
            self.base,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdEncodingRange:
        result = copy(self)
        memo[id(self)] = result
        result.first = deepcopy(self.first, memo)
        result.last = deepcopy(self.last, memo)
        result.base = deepcopy(self.base, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdEncodingRange):
            return NotImplemented
        return self.first == other.first and self.last == other.last and self.base == other.base

    def __repr__(self) -> str:
        return f'SfdEncodingRange(first={self.first!r}, last={self.last!r}, base={self.base!r})'

    def copy(self) -> SfdEncodingRange:
        return copy(self)

    def deepcopy(self) -> SfdEncodingRange:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdEncodingRange:
        from sfdfont._encoding import decode_encoding_range

        return decode_encoding_range(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._encoding import encode_encoding_range

        return encode_encoding_range(self)


class SfdEncodingRemap:
    ranges: list[SfdEncodingRange]

    def __init__(
        self,
        ranges: list[SfdEncodingRange] | None = None,
    ) -> None:
        self.ranges = ranges if ranges is not None else []

    def __copy__(self) -> SfdEncodingRemap:
        return SfdEncodingRemap(
            self.ranges,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdEncodingRemap:
        result = copy(self)
        memo[id(self)] = result
        result.ranges = deepcopy(self.ranges, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdEncodingRemap):
            return NotImplemented
        return self.ranges == other.ranges

    def __repr__(self) -> str:
        return f'SfdEncodingRemap(ranges={self.ranges!r})'

    def copy(self) -> SfdEncodingRemap:
        return copy(self)

    def deepcopy(self) -> SfdEncodingRemap:
        return deepcopy(self)

    @staticmethod
    def from_records(records: Iterable[SfdRecord]) -> SfdEncodingRemap:
        from sfdfont._encoding import decode_encoding_remap

        return decode_encoding_remap(records)

    def to_records(self) -> list[SfdRecord]:
        from sfdfont._encoding import encode_encoding_remap

        return encode_encoding_remap(self)
