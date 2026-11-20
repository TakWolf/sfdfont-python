from __future__ import annotations

from copy import copy, deepcopy
from typing import Any


class SfdPoint:
    """One SFD m/l/c operation; control coordinates retain their file meaning.

    The layer's quadratic flag determines curve order, including for c commands.
    Closing endpoints and the force-open flag are retained without normalization.
    """

    x: float
    y: float
    command: str
    controls: tuple[float, ...]
    flags: int
    hint_mask: bytes | None
    ttf_index: int | None
    next_cp_index: int | None
    name: str | None

    def __init__(
        self,
        x: float,
        y: float,
        command: str = 'm',
        controls: tuple[float, ...] = (),
        flags: int = 0,
        hint_mask: bytes | None = None,
        ttf_index: int | None = None,
        next_cp_index: int | None = None,
        name: str | None = None,
    ) -> None:
        self.x = x
        self.y = y
        self.command = command
        self.controls = controls
        self.flags = flags
        self.hint_mask = hint_mask
        self.ttf_index = ttf_index
        self.next_cp_index = next_cp_index
        self.name = name

    def __copy__(self) -> SfdPoint:
        return SfdPoint(
            self.x,
            self.y,
            self.command,
            self.controls,
            self.flags,
            self.hint_mask,
            self.ttf_index,
            self.next_cp_index,
            self.name,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdPoint:
        copied = copy(self)
        memo[id(self)] = copied
        copied.x = deepcopy(self.x, memo)
        copied.y = deepcopy(self.y, memo)
        copied.command = deepcopy(self.command, memo)
        copied.controls = deepcopy(self.controls, memo)
        copied.flags = deepcopy(self.flags, memo)
        copied.hint_mask = deepcopy(self.hint_mask, memo)
        copied.ttf_index = deepcopy(self.ttf_index, memo)
        copied.next_cp_index = deepcopy(self.next_cp_index, memo)
        copied.name = deepcopy(self.name, memo)
        return copied

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdPoint):
            return NotImplemented
        return (
            self.x == other.x
            and self.y == other.y
            and self.command == other.command
            and self.controls == other.controls
            and self.flags == other.flags
            and self.hint_mask == other.hint_mask
            and self.ttf_index == other.ttf_index
            and self.next_cp_index == other.next_cp_index
            and self.name == other.name
        )

    def __repr__(self) -> str:
        return (
            f'SfdPoint('
            f'x={self.x!r}, '
            f'y={self.y!r}, '
            f'command={self.command!r}, '
            f'controls={self.controls!r}, '
            f'flags={self.flags!r}, '
            f'hint_mask={self.hint_mask!r}, '
            f'ttf_index={self.ttf_index!r}, '
            f'next_cp_index={self.next_cp_index!r}, '
            f'name={self.name!r}'
            f')'
        )

    def copy(self) -> SfdPoint:
        return copy(self)

    def deepcopy(self) -> SfdPoint:
        return deepcopy(self)


class SfdSpiroPoint:
    x: float
    y: float
    kind: str

    def __init__(self, x: float, y: float, kind: str) -> None:
        self.x = x
        self.y = y
        self.kind = kind

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdSpiroPoint):
            return NotImplemented
        return self.x == other.x and self.y == other.y and self.kind == other.kind

    def copy(self) -> SfdSpiroPoint:
        return copy(self)

    def deepcopy(self) -> SfdSpiroPoint:
        return deepcopy(self)


class SfdContour:
    points: list[SfdPoint]
    name: str | None
    flags: int
    start_offset: int
    spiro: list[SfdSpiroPoint]

    def __init__(
        self,
        points: list[SfdPoint] | None = None,
        name: str | None = None,
        flags: int = 0,
        start_offset: int = 0,
        spiro: list[SfdSpiroPoint] | None = None,
    ) -> None:
        self.points = points if points is not None else []
        self.name = name
        self.flags = flags
        self.start_offset = start_offset
        self.spiro = spiro if spiro is not None else []

    def __copy__(self) -> SfdContour:
        return SfdContour(
            self.points,
            self.name,
            self.flags,
            self.start_offset,
            self.spiro,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdContour:
        copied = copy(self)
        memo[id(self)] = copied
        copied.points = deepcopy(self.points, memo)
        copied.name = deepcopy(self.name, memo)
        copied.flags = self.flags
        copied.start_offset = self.start_offset
        copied.spiro = deepcopy(self.spiro, memo)
        return copied

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdContour):
            return NotImplemented
        return (
            self.points == other.points
            and self.name == other.name
            and self.flags == other.flags
            and self.start_offset == other.start_offset
            and self.spiro == other.spiro
        )

    def __repr__(self) -> str:
        return (
            f'SfdContour(points={self.points!r}, name={self.name!r}, flags={self.flags!r}, '
            f'start_offset={self.start_offset!r}, spiro={self.spiro!r})'
        )

    def copy(self) -> SfdContour:
        return copy(self)

    def deepcopy(self) -> SfdContour:
        return deepcopy(self)
