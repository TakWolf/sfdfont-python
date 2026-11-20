from __future__ import annotations

from copy import copy, deepcopy
from typing import Any

from sfdfont.record import SfdRecord


class SfdPanose:
    values: list[int]

    def __init__(
        self,
        values: list[int] | None = None,
    ) -> None:
        self.values = values if values is not None else [0] * 10

    def __copy__(self) -> SfdPanose:
        return SfdPanose(
            self.values,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdPanose:
        result = copy(self)
        memo[id(self)] = result
        result.values = deepcopy(self.values, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdPanose):
            return NotImplemented
        return self.values == other.values

    def __repr__(self) -> str:
        return f'SfdPanose(values={self.values!r})'

    def copy(self) -> SfdPanose:
        return copy(self)

    def deepcopy(self) -> SfdPanose:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdPanose:
        from sfdfont._os2 import decode_panose

        return decode_panose(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._os2 import encode_panose

        return encode_panose(self)


class SfdOs2Mask:
    keyword: str
    value: int

    def __init__(
        self,
        keyword: str = 'OS2UnicodeRanges:',
        value: int = 0,
    ) -> None:
        self.keyword = keyword
        self.value = value

    def __copy__(self) -> SfdOs2Mask:
        return SfdOs2Mask(
            self.keyword,
            self.value,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdOs2Mask:
        result = copy(self)
        memo[id(self)] = result
        result.keyword = deepcopy(self.keyword, memo)
        result.value = deepcopy(self.value, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdOs2Mask):
            return NotImplemented
        return self.keyword == other.keyword and self.value == other.value

    def __repr__(self) -> str:
        return f'SfdOs2Mask(keyword={self.keyword!r}, value={self.value!r})'

    def copy(self) -> SfdOs2Mask:
        return copy(self)

    def deepcopy(self) -> SfdOs2Mask:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdOs2Mask:
        from sfdfont._os2 import decode_os2_mask

        return decode_os2_mask(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._os2 import encode_os2_mask

        return encode_os2_mask(self)


class SfdOs2Vendor:
    vendor: bytes

    def __init__(
        self,
        vendor: bytes = b'    ',
    ) -> None:
        self.vendor = vendor

    def __copy__(self) -> SfdOs2Vendor:
        return SfdOs2Vendor(
            self.vendor,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdOs2Vendor:
        result = copy(self)
        memo[id(self)] = result
        result.vendor = deepcopy(self.vendor, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdOs2Vendor):
            return NotImplemented
        return self.vendor == other.vendor

    def __repr__(self) -> str:
        return f'SfdOs2Vendor(vendor={self.vendor!r})'

    def copy(self) -> SfdOs2Vendor:
        return copy(self)

    def deepcopy(self) -> SfdOs2Vendor:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdOs2Vendor:
        from sfdfont._os2 import decode_os2_vendor

        return decode_os2_vendor(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._os2 import encode_os2_vendor

        return encode_os2_vendor(self)
