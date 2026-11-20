from __future__ import annotations

from copy import copy, deepcopy
from typing import Any

from sfdfont.record import SfdRecord


class SfdSfntRevision:
    value: int

    def __init__(
        self,
        value: int = 0x00010000,
    ) -> None:
        self.value = value

    def __copy__(self) -> SfdSfntRevision:
        return SfdSfntRevision(
            self.value,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdSfntRevision:
        result = copy(self)
        memo[id(self)] = result
        result.value = deepcopy(self.value, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdSfntRevision):
            return NotImplemented
        return self.value == other.value

    def __repr__(self) -> str:
        return f'SfdSfntRevision(value={self.value!r})'

    def copy(self) -> SfdSfntRevision:
        return copy(self)

    def deepcopy(self) -> SfdSfntRevision:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdSfntRevision:
        from sfdfont._revision import decode_revision

        return decode_revision(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._revision import encode_revision

        return encode_revision(self)
