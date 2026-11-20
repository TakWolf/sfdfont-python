from __future__ import annotations

from copy import copy, deepcopy
from typing import Any

from sfdfont.record import SfdRecord


class SfdGaspRange:
    ppem: int
    flags: int

    def __init__(
        self,
        ppem: int = 65535,
        flags: int = 3,
    ) -> None:
        self.ppem = ppem
        self.flags = flags

    def __copy__(self) -> SfdGaspRange:
        return SfdGaspRange(
            self.ppem,
            self.flags,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdGaspRange:
        result = copy(self)
        memo[id(self)] = result
        result.ppem = deepcopy(self.ppem, memo)
        result.flags = deepcopy(self.flags, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdGaspRange):
            return NotImplemented
        return self.ppem == other.ppem and self.flags == other.flags

    def __repr__(self) -> str:
        return f'SfdGaspRange(ppem={self.ppem!r}, flags={self.flags!r})'

    def copy(self) -> SfdGaspRange:
        return copy(self)

    def deepcopy(self) -> SfdGaspRange:
        return deepcopy(self)


class SfdGaspTable:
    ranges: list[SfdGaspRange]
    version: int

    def __init__(
        self,
        ranges: list[SfdGaspRange] | None = None,
        version: int = 0,
    ) -> None:
        self.ranges = ranges if ranges is not None else []
        self.version = version

    def __copy__(self) -> SfdGaspTable:
        return SfdGaspTable(
            self.ranges,
            self.version,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdGaspTable:
        result = copy(self)
        memo[id(self)] = result
        result.ranges = deepcopy(self.ranges, memo)
        result.version = deepcopy(self.version, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdGaspTable):
            return NotImplemented
        return self.ranges == other.ranges and self.version == other.version

    def __repr__(self) -> str:
        return f'SfdGaspTable(ranges={self.ranges!r}, version={self.version!r})'

    def copy(self) -> SfdGaspTable:
        return copy(self)

    def deepcopy(self) -> SfdGaspTable:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdGaspTable:
        from sfdfont._gasp import decode_gasp

        return decode_gasp(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._gasp import encode_gasp

        return encode_gasp(self)
