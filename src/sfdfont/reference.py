from __future__ import annotations

from copy import copy, deepcopy
from typing import Any


class SfdReference:
    target: int
    unicode: int
    selected: bool
    transform: tuple[float, ...]
    flags: int
    point_match: tuple[int, int] | None
    point_match_outdated: bool
    encoded: bool

    def __init__(
        self,
        target: int,
        unicode: int = -1,
        selected: bool = False,
        transform: tuple[float, ...] = (1, 0, 0, 1, 0, 0),
        flags: int = 0,
        point_match: tuple[int, int] | None = None,
        point_match_outdated: bool = False,
        encoded: bool = False,
    ) -> None:
        self.target = target
        self.unicode = unicode
        self.selected = selected
        self.transform = transform
        self.flags = flags
        self.point_match = point_match
        self.point_match_outdated = point_match_outdated
        self.encoded = encoded

    def __copy__(self) -> SfdReference:
        return SfdReference(
            self.target,
            self.unicode,
            self.selected,
            self.transform,
            self.flags,
            self.point_match,
            self.point_match_outdated,
            self.encoded,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdReference:
        copied = copy(self)
        memo[id(self)] = copied
        copied.target = deepcopy(self.target, memo)
        copied.unicode = deepcopy(self.unicode, memo)
        copied.selected = deepcopy(self.selected, memo)
        copied.transform = deepcopy(self.transform, memo)
        copied.flags = deepcopy(self.flags, memo)
        copied.point_match = deepcopy(self.point_match, memo)
        copied.point_match_outdated = deepcopy(self.point_match_outdated, memo)
        copied.encoded = deepcopy(self.encoded, memo)
        return copied

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdReference):
            return NotImplemented
        return (
            self.target == other.target
            and self.unicode == other.unicode
            and self.selected == other.selected
            and self.transform == other.transform
            and self.flags == other.flags
            and self.point_match == other.point_match
            and self.point_match_outdated == other.point_match_outdated
            and self.encoded == other.encoded
        )

    def __repr__(self) -> str:
        return (
            f'SfdReference('
            f'target={self.target!r}, '
            f'unicode={self.unicode!r}, '
            f'selected={self.selected!r}, '
            f'transform={self.transform!r}, '
            f'flags={self.flags!r}, '
            f'point_match={self.point_match!r}, '
            f'point_match_outdated={self.point_match_outdated!r}, '
            f'encoded={self.encoded!r}'
            f')'
        )

    def copy(self) -> SfdReference:
        return copy(self)

    def deepcopy(self) -> SfdReference:
        return deepcopy(self)
