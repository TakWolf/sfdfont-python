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
    ) -> None:
        self.x = x
        self.y = y
        self.command = command
        self.controls = controls
        self.flags = flags
        self.hint_mask = hint_mask
        self.ttf_index = ttf_index
        self.next_cp_index = next_cp_index

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
            f'next_cp_index={self.next_cp_index!r}'
            f')'
        )

    def copy(self) -> SfdPoint:
        return copy(self)

    def deepcopy(self) -> SfdPoint:
        return deepcopy(self)


class SfdContour:
    points: list[SfdPoint]

    def __init__(
        self,
        points: list[SfdPoint] | None = None,
    ) -> None:
        self.points = points if points is not None else []

    def __copy__(self) -> SfdContour:
        return SfdContour(
            self.points,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdContour:
        copied = copy(self)
        memo[id(self)] = copied
        copied.points = deepcopy(self.points, memo)
        return copied

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdContour):
            return NotImplemented
        return self.points == other.points

    def __repr__(self) -> str:
        return f'SfdContour(points={self.points!r})'

    def copy(self) -> SfdContour:
        return copy(self)

    def deepcopy(self) -> SfdContour:
        return deepcopy(self)
