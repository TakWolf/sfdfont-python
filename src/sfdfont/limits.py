from __future__ import annotations

from copy import copy
from typing import Any


class SfdReadLimits:
    """Per-document limits, checked before allocating decoded payloads."""

    max_bytes: int
    max_glyphs: int
    max_points: int
    max_payload_bytes: int

    def __init__(
        self,
        max_bytes: int = 64 * 1024 * 1024,
        max_glyphs: int = 100_000,
        max_points: int = 2_000_000,
        max_payload_bytes: int = 64 * 1024 * 1024,
    ) -> None:
        if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes < 0:
            raise ValueError('max_bytes must be a nonnegative integer')
        object.__setattr__(self, 'max_bytes', max_bytes)
        if isinstance(max_glyphs, bool) or not isinstance(max_glyphs, int) or max_glyphs < 0:
            raise ValueError('max_glyphs must be a nonnegative integer')
        object.__setattr__(self, 'max_glyphs', max_glyphs)
        if isinstance(max_points, bool) or not isinstance(max_points, int) or max_points < 0:
            raise ValueError('max_points must be a nonnegative integer')
        object.__setattr__(self, 'max_points', max_points)
        if isinstance(max_payload_bytes, bool) or not isinstance(max_payload_bytes, int) or max_payload_bytes < 0:
            raise ValueError('max_payload_bytes must be a nonnegative integer')
        object.__setattr__(self, 'max_payload_bytes', max_payload_bytes)

    def __copy__(self) -> SfdReadLimits:
        return SfdReadLimits(
            self.max_bytes,
            self.max_glyphs,
            self.max_points,
            self.max_payload_bytes,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdReadLimits:
        return copy(self)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdReadLimits):
            return NotImplemented
        return (
            self.max_bytes == other.max_bytes
            and self.max_glyphs == other.max_glyphs
            and self.max_points == other.max_points
            and self.max_payload_bytes == other.max_payload_bytes
        )

    def __repr__(self) -> str:
        return (
            f'SfdReadLimits('
            f'max_bytes={self.max_bytes!r}, '
            f'max_glyphs={self.max_glyphs!r}, '
            f'max_points={self.max_points!r}, '
            f'max_payload_bytes={self.max_payload_bytes!r}'
            f')'
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.max_bytes,
                self.max_glyphs,
                self.max_points,
                self.max_payload_bytes,
            )
        )

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError('SfdReadLimits is immutable')

    def __delattr__(self, name: str) -> None:
        raise AttributeError('SfdReadLimits is immutable')
