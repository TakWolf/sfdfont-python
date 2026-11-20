from __future__ import annotations

from copy import copy, deepcopy
from typing import Any

from sfdfont.record import SfdRecord


class SfdWoffMetadata:
    text: str

    def __init__(
        self,
        text: str = '',
    ) -> None:
        self.text = text

    def __copy__(self) -> SfdWoffMetadata:
        return SfdWoffMetadata(
            self.text,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdWoffMetadata:
        result = copy(self)
        memo[id(self)] = result
        result.text = deepcopy(self.text, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdWoffMetadata):
            return NotImplemented
        return self.text == other.text

    def __repr__(self) -> str:
        return f'SfdWoffMetadata(text={self.text!r})'

    def copy(self) -> SfdWoffMetadata:
        return copy(self)

    def deepcopy(self) -> SfdWoffMetadata:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdWoffMetadata:
        from sfdfont._woff import decode_woff_metadata

        return decode_woff_metadata(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._woff import encode_woff_metadata

        return encode_woff_metadata(self)
