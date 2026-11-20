from __future__ import annotations

from copy import copy, deepcopy
from typing import Any

from sfdfont.record import SfdRecord


class SfdTexData:
    kind: int
    design_size: int
    parameters: list[int]

    def __init__(
        self,
        kind: int = 1,
        design_size: int = 0,
        parameters: list[int] | None = None,
    ) -> None:
        self.kind = kind
        self.design_size = design_size
        self.parameters = parameters if parameters is not None else [0] * 22

    def __copy__(self) -> SfdTexData:
        return SfdTexData(
            self.kind,
            self.design_size,
            self.parameters,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdTexData:
        result = copy(self)
        memo[id(self)] = result
        result.kind = deepcopy(self.kind, memo)
        result.design_size = deepcopy(self.design_size, memo)
        result.parameters = deepcopy(self.parameters, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdTexData):
            return NotImplemented
        return self.kind == other.kind and self.design_size == other.design_size and self.parameters == other.parameters

    def __repr__(self) -> str:
        return f'SfdTexData(kind={self.kind!r}, design_size={self.design_size!r}, parameters={self.parameters!r})'

    def copy(self) -> SfdTexData:
        return copy(self)

    def deepcopy(self) -> SfdTexData:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdTexData:
        from sfdfont._tex import decode_tex_data

        return decode_tex_data(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._tex import encode_tex_data

        return encode_tex_data(self)


class SfdTexMetrics:
    height: int
    depth: int
    legacy: tuple[int, int] | None

    def __init__(
        self,
        height: int = 0x7FFF,
        depth: int = 0x7FFF,
        legacy: tuple[int, int] | None = None,
    ) -> None:
        self.height = height
        self.depth = depth
        self.legacy = legacy

    def __copy__(self) -> SfdTexMetrics:
        return SfdTexMetrics(
            self.height,
            self.depth,
            self.legacy,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdTexMetrics:
        result = copy(self)
        memo[id(self)] = result
        result.height = deepcopy(self.height, memo)
        result.depth = deepcopy(self.depth, memo)
        result.legacy = deepcopy(self.legacy, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdTexMetrics):
            return NotImplemented
        return self.height == other.height and self.depth == other.depth and self.legacy == other.legacy

    def __repr__(self) -> str:
        return f'SfdTexMetrics(height={self.height!r}, depth={self.depth!r}, legacy={self.legacy!r})'

    def copy(self) -> SfdTexMetrics:
        return copy(self)

    def deepcopy(self) -> SfdTexMetrics:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdTexMetrics:
        from sfdfont._tex import decode_tex_metrics

        return decode_tex_metrics(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._tex import encode_tex_metrics

        return encode_tex_metrics(self)
