from __future__ import annotations

from copy import copy, deepcopy
from typing import Any

from sfdfont.record import SfdRecord


class SfdStyleName:
    language: int
    name: str

    def __init__(
        self,
        language: int = 0x0409,
        name: str = '',
    ) -> None:
        self.language = language
        self.name = name

    def __copy__(self) -> SfdStyleName:
        return SfdStyleName(
            self.language,
            self.name,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdStyleName:
        result = copy(self)
        memo[id(self)] = result
        result.language = deepcopy(self.language, memo)
        result.name = deepcopy(self.name, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdStyleName):
            return NotImplemented
        return self.language == other.language and self.name == other.name

    def __repr__(self) -> str:
        return f'SfdStyleName(language={self.language!r}, name={self.name!r})'

    def copy(self) -> SfdStyleName:
        return copy(self)

    def deepcopy(self) -> SfdStyleName:
        return deepcopy(self)


class SfdDesignSize:
    size: int
    range: tuple[int, int] | None
    style_id: int | None
    names: list[SfdStyleName]

    def __init__(
        self,
        size: int = 0,
        range: tuple[int, int] | None = None,
        style_id: int | None = None,
        names: list[SfdStyleName] | None = None,
    ) -> None:
        self.size = size
        self.range = range
        self.style_id = style_id
        self.names = names if names is not None else []

    def __copy__(self) -> SfdDesignSize:
        return SfdDesignSize(
            self.size,
            self.range,
            self.style_id,
            self.names,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdDesignSize:
        result = copy(self)
        memo[id(self)] = result
        result.size = deepcopy(self.size, memo)
        result.range = deepcopy(self.range, memo)
        result.style_id = deepcopy(self.style_id, memo)
        result.names = deepcopy(self.names, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdDesignSize):
            return NotImplemented
        return (
            self.size == other.size
            and self.range == other.range
            and self.style_id == other.style_id
            and self.names == other.names
        )

    def __repr__(self) -> str:
        return (
            f'SfdDesignSize(size={self.size!r}, range={self.range!r}, style_id={self.style_id!r}, names={self.names!r})'
        )

    def copy(self) -> SfdDesignSize:
        return copy(self)

    def deepcopy(self) -> SfdDesignSize:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdDesignSize:
        from sfdfont._size import decode_design_size

        return decode_design_size(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._size import encode_design_size

        return encode_design_size(self)
