from __future__ import annotations

from copy import copy, deepcopy
from typing import Any


class SfdRecord:
    """An uninterpreted record. Value may include a known, terminated block."""

    keyword: str
    value: bytes

    def __init__(
        self,
        keyword: str,
        value: bytes = b'',
    ) -> None:
        self.keyword = keyword
        self.value = value

    def __copy__(self) -> SfdRecord:
        return SfdRecord(
            self.keyword,
            self.value,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdRecord:
        copied = copy(self)
        memo[id(self)] = copied
        copied.keyword = deepcopy(self.keyword, memo)
        copied.value = deepcopy(self.value, memo)
        return copied

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdRecord):
            return NotImplemented
        return self.keyword == other.keyword and self.value == other.value

    def __repr__(self) -> str:
        return f'SfdRecord(keyword={self.keyword!r}, value={self.value!r})'

    def copy(self) -> SfdRecord:
        return copy(self)

    def deepcopy(self) -> SfdRecord:
        return deepcopy(self)
