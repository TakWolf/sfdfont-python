from __future__ import annotations

from copy import copy, deepcopy
from typing import Any

from sfdfont.record import SfdRecord


class SfdMarkGroup:
    name: str
    glyphs: list[str]

    def __init__(
        self,
        name: str = '',
        glyphs: list[str] | None = None,
    ) -> None:
        self.name = name
        self.glyphs = glyphs if glyphs is not None else []

    def __copy__(self) -> SfdMarkGroup:
        return SfdMarkGroup(
            self.name,
            self.glyphs,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdMarkGroup:
        result = copy(self)
        memo[id(self)] = result
        result.name = deepcopy(self.name, memo)
        result.glyphs = deepcopy(self.glyphs, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdMarkGroup):
            return NotImplemented
        return self.name == other.name and self.glyphs == other.glyphs

    def __repr__(self) -> str:
        return f'SfdMarkGroup(name={self.name!r}, glyphs={self.glyphs!r})'

    def copy(self) -> SfdMarkGroup:
        return copy(self)

    def deepcopy(self) -> SfdMarkGroup:
        return deepcopy(self)


class SfdMarkClasses:
    classes: list[SfdMarkGroup]

    def __init__(
        self,
        classes: list[SfdMarkGroup] | None = None,
    ) -> None:
        self.classes = classes if classes is not None else []

    def __copy__(self) -> SfdMarkClasses:
        return SfdMarkClasses(
            self.classes,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdMarkClasses:
        result = copy(self)
        memo[id(self)] = result
        result.classes = deepcopy(self.classes, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdMarkClasses):
            return NotImplemented
        return self.classes == other.classes

    def __repr__(self) -> str:
        return f'SfdMarkClasses(classes={self.classes!r})'

    def copy(self) -> SfdMarkClasses:
        return copy(self)

    def deepcopy(self) -> SfdMarkClasses:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdMarkClasses:
        from sfdfont._marks import decode_classes

        return decode_classes(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._marks import encode_classes

        return encode_classes(self)


class SfdMarkSets:
    sets: list[SfdMarkGroup]

    def __init__(
        self,
        sets: list[SfdMarkGroup] | None = None,
    ) -> None:
        self.sets = sets if sets is not None else []

    def __copy__(self) -> SfdMarkSets:
        return SfdMarkSets(
            self.sets,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdMarkSets:
        result = copy(self)
        memo[id(self)] = result
        result.sets = deepcopy(self.sets, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdMarkSets):
            return NotImplemented
        return self.sets == other.sets

    def __repr__(self) -> str:
        return f'SfdMarkSets(sets={self.sets!r})'

    def copy(self) -> SfdMarkSets:
        return copy(self)

    def deepcopy(self) -> SfdMarkSets:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdMarkSets:
        from sfdfont._marks import decode_sets

        return decode_sets(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._marks import encode_sets

        return encode_sets(self)
