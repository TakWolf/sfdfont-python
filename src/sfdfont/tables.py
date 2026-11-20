from __future__ import annotations

from copy import copy, deepcopy
from typing import Any

from sfdfont.record import SfdRecord


class SfdPrivateEntry:
    key: str
    value: bytes

    def __init__(
        self,
        key: str = 'BlueValues',
        value: bytes = b'[]',
    ) -> None:
        self.key = key
        self.value = value

    def __copy__(self) -> SfdPrivateEntry:
        return SfdPrivateEntry(
            self.key,
            self.value,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdPrivateEntry:
        result = copy(self)
        memo[id(self)] = result
        result.key = deepcopy(self.key, memo)
        result.value = deepcopy(self.value, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdPrivateEntry):
            return NotImplemented
        return self.key == other.key and self.value == other.value

    def __repr__(self) -> str:
        return f'SfdPrivateEntry(key={self.key!r}, value={self.value!r})'

    def copy(self) -> SfdPrivateEntry:
        return copy(self)

    def deepcopy(self) -> SfdPrivateEntry:
        return deepcopy(self)


class SfdPrivateDict:
    entries: list[SfdPrivateEntry]

    def __init__(
        self,
        entries: list[SfdPrivateEntry] | None = None,
    ) -> None:
        self.entries = entries if entries is not None else []

    def __copy__(self) -> SfdPrivateDict:
        return SfdPrivateDict(
            self.entries,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdPrivateDict:
        result = copy(self)
        memo[id(self)] = result
        result.entries = deepcopy(self.entries, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdPrivateDict):
            return NotImplemented
        return self.entries == other.entries

    def __repr__(self) -> str:
        return f'SfdPrivateDict(entries={self.entries!r})'

    def copy(self) -> SfdPrivateDict:
        return copy(self)

    def deepcopy(self) -> SfdPrivateDict:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdPrivateDict:
        from sfdfont._tables import decode_private

        return decode_private(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._tables import encode_private

        return encode_private(self)


class SfdShortTableWord:
    value: int
    name: str | None

    def __init__(
        self,
        value: int = 0,
        name: str | None = None,
    ) -> None:
        self.value = value
        self.name = name

    def __copy__(self) -> SfdShortTableWord:
        return SfdShortTableWord(
            self.value,
            self.name,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdShortTableWord:
        result = copy(self)
        memo[id(self)] = result
        result.value = deepcopy(self.value, memo)
        result.name = deepcopy(self.name, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdShortTableWord):
            return NotImplemented
        return self.value == other.value and self.name == other.name

    def __repr__(self) -> str:
        return f'SfdShortTableWord(value={self.value!r}, name={self.name!r})'

    def copy(self) -> SfdShortTableWord:
        return copy(self)

    def deepcopy(self) -> SfdShortTableWord:
        return deepcopy(self)


class SfdShortTable:
    tag: str
    words: list[SfdShortTableWord]

    def __init__(
        self,
        tag: str = 'cvt ',
        words: list[SfdShortTableWord] | None = None,
    ) -> None:
        self.tag = tag
        self.words = words if words is not None else []

    def __copy__(self) -> SfdShortTable:
        return SfdShortTable(
            self.tag,
            self.words,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdShortTable:
        result = copy(self)
        memo[id(self)] = result
        result.tag = deepcopy(self.tag, memo)
        result.words = deepcopy(self.words, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdShortTable):
            return NotImplemented
        return self.tag == other.tag and self.words == other.words

    def __repr__(self) -> str:
        return f'SfdShortTable(tag={self.tag!r}, words={self.words!r})'

    def copy(self) -> SfdShortTable:
        return copy(self)

    def deepcopy(self) -> SfdShortTable:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdShortTable:
        from sfdfont._tables import decode_short_table

        return decode_short_table(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._tables import encode_short_table

        return encode_short_table(self)
