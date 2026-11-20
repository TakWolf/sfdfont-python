from __future__ import annotations

from copy import copy, deepcopy
from typing import Any


class SfdPayload:
    """Decoded binary payload with its original header parameters.

    Image data is retained, including old palette/RLE data; it is not rendered.
    TrueType instructions and tables are retained, not executed or assembled.
    Obsolete OrigType1/BeginSubrs blocks have an empty terminator; subroutine
    header lengths are normalized and the decoded bytes remain concatenated.
    """

    keyword: str
    parameters: bytes
    data: bytes
    terminator: str

    def __init__(
        self,
        keyword: str,
        parameters: bytes,
        data: bytes,
        terminator: str,
    ) -> None:
        self.keyword = keyword
        self.parameters = parameters
        self.data = data
        self.terminator = terminator

    def __copy__(self) -> SfdPayload:
        return SfdPayload(
            self.keyword,
            self.parameters,
            self.data,
            self.terminator,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdPayload:
        copied = copy(self)
        memo[id(self)] = copied
        copied.keyword = deepcopy(self.keyword, memo)
        copied.parameters = deepcopy(self.parameters, memo)
        copied.data = deepcopy(self.data, memo)
        copied.terminator = deepcopy(self.terminator, memo)
        return copied

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdPayload):
            return NotImplemented
        return (
            self.keyword == other.keyword
            and self.parameters == other.parameters
            and self.data == other.data
            and self.terminator == other.terminator
        )

    def __repr__(self) -> str:
        return (
            f'SfdPayload('
            f'keyword={self.keyword!r}, '
            f'parameters={self.parameters!r}, '
            f'data={self.data!r}, '
            f'terminator={self.terminator!r}'
            f')'
        )

    def copy(self) -> SfdPayload:
        return copy(self)

    def deepcopy(self) -> SfdPayload:
        return deepcopy(self)
