from __future__ import annotations

from copy import copy, deepcopy
from typing import Any

from sfdfont.outline import SfdContour
from sfdfont.record import SfdRecord
from sfdfont.reference import SfdReference


class SfdLayerInfo:
    index: int
    quadratic: bool
    name: str
    background: bool
    ufo_path: str | None

    def __init__(
        self,
        index: int,
        quadratic: bool = False,
        name: str = 'Fore',
        background: bool = False,
        ufo_path: str | None = None,
    ) -> None:
        self.index = index
        self.quadratic = quadratic
        self.name = name
        self.background = background
        self.ufo_path = ufo_path

    def __copy__(self) -> SfdLayerInfo:
        return SfdLayerInfo(
            self.index,
            self.quadratic,
            self.name,
            self.background,
            self.ufo_path,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdLayerInfo:
        copied = copy(self)
        memo[id(self)] = copied
        copied.index = deepcopy(self.index, memo)
        copied.quadratic = deepcopy(self.quadratic, memo)
        copied.name = deepcopy(self.name, memo)
        copied.background = deepcopy(self.background, memo)
        copied.ufo_path = deepcopy(self.ufo_path, memo)
        return copied

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdLayerInfo):
            return NotImplemented
        return (
            self.index == other.index
            and self.quadratic == other.quadratic
            and self.name == other.name
            and self.background == other.background
            and self.ufo_path == other.ufo_path
        )

    def __repr__(self) -> str:
        return (
            f'SfdLayerInfo('
            f'index={self.index!r}, '
            f'quadratic={self.quadratic!r}, '
            f'name={self.name!r}, '
            f'background={self.background!r}, '
            f'ufo_path={self.ufo_path!r}'
            f')'
        )

    def copy(self) -> SfdLayerInfo:
        return copy(self)

    def deepcopy(self) -> SfdLayerInfo:
        return deepcopy(self)


class SfdLayer:
    index: int
    contours: list[SfdContour]
    references: list[SfdReference]
    records: list[SfdRecord]

    def __init__(
        self,
        index: int = 1,
        contours: list[SfdContour] | None = None,
        references: list[SfdReference] | None = None,
        records: list[SfdRecord] | None = None,
    ) -> None:
        self.index = index
        self.contours = contours if contours is not None else []
        self.references = references if references is not None else []
        self.records = records if records is not None else []

    def __copy__(self) -> SfdLayer:
        return SfdLayer(
            self.index,
            self.contours,
            self.references,
            self.records,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdLayer:
        copied = copy(self)
        memo[id(self)] = copied
        copied.index = deepcopy(self.index, memo)
        copied.contours = deepcopy(self.contours, memo)
        copied.references = deepcopy(self.references, memo)
        copied.records = deepcopy(self.records, memo)
        return copied

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdLayer):
            return NotImplemented
        return (
            self.index == other.index
            and self.contours == other.contours
            and self.references == other.references
            and self.records == other.records
        )

    def __repr__(self) -> str:
        return (
            f'SfdLayer('
            f'index={self.index!r}, '
            f'contours={self.contours!r}, '
            f'references={self.references!r}, '
            f'records={self.records!r}'
            f')'
        )

    def copy(self) -> SfdLayer:
        return copy(self)

    def deepcopy(self) -> SfdLayer:
        return deepcopy(self)
