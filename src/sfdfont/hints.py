from __future__ import annotations

from copy import copy, deepcopy
from typing import Any

from sfdfont.record import SfdRecord


class SfdStemHint:
    start: float
    width: float
    ghost: bool
    instances: list[tuple[float, float]]

    def __init__(
        self,
        start: float = 0,
        width: float = 0,
        ghost: bool = False,
        instances: list[tuple[float, float]] | None = None,
    ) -> None:
        self.start = start
        self.width = width
        self.ghost = ghost
        self.instances = instances if instances is not None else []

    def __copy__(self) -> SfdStemHint:
        return SfdStemHint(
            self.start,
            self.width,
            self.ghost,
            self.instances,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdStemHint:
        result = copy(self)
        memo[id(self)] = result
        result.start = deepcopy(self.start, memo)
        result.width = deepcopy(self.width, memo)
        result.ghost = deepcopy(self.ghost, memo)
        result.instances = deepcopy(self.instances, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdStemHint):
            return NotImplemented
        return (
            self.start == other.start
            and self.width == other.width
            and self.ghost == other.ghost
            and self.instances == other.instances
        )

    def __repr__(self) -> str:
        return (
            f'SfdStemHint('
            f'start={self.start!r}, '
            f'width={self.width!r}, '
            f'ghost={self.ghost!r}, '
            f'instances={self.instances!r}'
            f')'
        )

    def copy(self) -> SfdStemHint:
        return copy(self)

    def deepcopy(self) -> SfdStemHint:
        return deepcopy(self)


class SfdStemHints:
    keyword: str
    hints: list[SfdStemHint]

    def __init__(
        self,
        keyword: str = 'HStem:',
        hints: list[SfdStemHint] | None = None,
    ) -> None:
        self.keyword = keyword
        self.hints = hints if hints is not None else []

    def __copy__(self) -> SfdStemHints:
        return SfdStemHints(
            self.keyword,
            self.hints,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdStemHints:
        result = copy(self)
        memo[id(self)] = result
        result.keyword = deepcopy(self.keyword, memo)
        result.hints = deepcopy(self.hints, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdStemHints):
            return NotImplemented
        return self.keyword == other.keyword and self.hints == other.hints

    def __repr__(self) -> str:
        return f'SfdStemHints(keyword={self.keyword!r}, hints={self.hints!r})'

    def copy(self) -> SfdStemHints:
        return copy(self)

    def deepcopy(self) -> SfdStemHints:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdStemHints:
        from sfdfont._hints import decode_stems

        return decode_stems(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._hints import encode_stems

        return encode_stems(self)


class SfdDiagonalHint:
    coordinates: tuple[float, ...]
    instances: list[tuple[float, float]]

    def __init__(
        self,
        coordinates: tuple[float, ...] = (0, 0, 0, 0, 1, 0),
        instances: list[tuple[float, float]] | None = None,
    ) -> None:
        self.coordinates = coordinates
        self.instances = instances if instances is not None else []

    def __copy__(self) -> SfdDiagonalHint:
        return SfdDiagonalHint(
            self.coordinates,
            self.instances,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdDiagonalHint:
        result = copy(self)
        memo[id(self)] = result
        result.coordinates = deepcopy(self.coordinates, memo)
        result.instances = deepcopy(self.instances, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdDiagonalHint):
            return NotImplemented
        return self.coordinates == other.coordinates and self.instances == other.instances

    def __repr__(self) -> str:
        return f'SfdDiagonalHint(coordinates={self.coordinates!r}, instances={self.instances!r})'

    def copy(self) -> SfdDiagonalHint:
        return copy(self)

    def deepcopy(self) -> SfdDiagonalHint:
        return deepcopy(self)


class SfdDiagonalHints:
    keyword: str
    hints: list[SfdDiagonalHint]

    def __init__(
        self,
        keyword: str = 'DStem2:',
        hints: list[SfdDiagonalHint] | None = None,
    ) -> None:
        self.keyword = keyword
        self.hints = hints if hints is not None else []

    def __copy__(self) -> SfdDiagonalHints:
        return SfdDiagonalHints(
            self.keyword,
            self.hints,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdDiagonalHints:
        result = copy(self)
        memo[id(self)] = result
        result.keyword = deepcopy(self.keyword, memo)
        result.hints = deepcopy(self.hints, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdDiagonalHints):
            return NotImplemented
        return self.keyword == other.keyword and self.hints == other.hints

    def __repr__(self) -> str:
        return f'SfdDiagonalHints(keyword={self.keyword!r}, hints={self.hints!r})'

    def copy(self) -> SfdDiagonalHints:
        return copy(self)

    def deepcopy(self) -> SfdDiagonalHints:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdDiagonalHints:
        from sfdfont._hints import decode_diagonals

        return decode_diagonals(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._hints import encode_diagonals

        return encode_diagonals(self)


class SfdCounterMasks:
    masks: list[bytes]

    def __init__(
        self,
        masks: list[bytes] | None = None,
    ) -> None:
        self.masks = masks if masks is not None else []

    def __copy__(self) -> SfdCounterMasks:
        return SfdCounterMasks(
            self.masks,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdCounterMasks:
        result = copy(self)
        memo[id(self)] = result
        result.masks = deepcopy(self.masks, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdCounterMasks):
            return NotImplemented
        return self.masks == other.masks

    def __repr__(self) -> str:
        return f'SfdCounterMasks(masks={self.masks!r})'

    def copy(self) -> SfdCounterMasks:
        return copy(self)

    def deepcopy(self) -> SfdCounterMasks:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdCounterMasks:
        from sfdfont._hints import decode_counter_masks

        return decode_counter_masks(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._hints import encode_counter_masks

        return encode_counter_masks(self)


class SfdMinimumDistance:
    axis: str
    first: int
    second: int

    def __init__(
        self,
        axis: str = 'x',
        first: int = -1,
        second: int = -1,
    ) -> None:
        self.axis = axis
        self.first = first
        self.second = second

    def __copy__(self) -> SfdMinimumDistance:
        return SfdMinimumDistance(
            self.axis,
            self.first,
            self.second,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdMinimumDistance:
        result = copy(self)
        memo[id(self)] = result
        result.axis = deepcopy(self.axis, memo)
        result.first = deepcopy(self.first, memo)
        result.second = deepcopy(self.second, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdMinimumDistance):
            return NotImplemented
        return self.axis == other.axis and self.first == other.first and self.second == other.second

    def __repr__(self) -> str:
        return f'SfdMinimumDistance(axis={self.axis!r}, first={self.first!r}, second={self.second!r})'

    def copy(self) -> SfdMinimumDistance:
        return copy(self)

    def deepcopy(self) -> SfdMinimumDistance:
        return deepcopy(self)


class SfdMinimumDistances:
    distances: list[SfdMinimumDistance]

    def __init__(
        self,
        distances: list[SfdMinimumDistance] | None = None,
    ) -> None:
        self.distances = distances if distances is not None else []

    def __copy__(self) -> SfdMinimumDistances:
        return SfdMinimumDistances(
            self.distances,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdMinimumDistances:
        result = copy(self)
        memo[id(self)] = result
        result.distances = deepcopy(self.distances, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdMinimumDistances):
            return NotImplemented
        return self.distances == other.distances

    def __repr__(self) -> str:
        return f'SfdMinimumDistances(distances={self.distances!r})'

    def copy(self) -> SfdMinimumDistances:
        return copy(self)

    def deepcopy(self) -> SfdMinimumDistances:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdMinimumDistances:
        from sfdfont._hints import decode_minimum_distances

        return decode_minimum_distances(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._hints import encode_minimum_distances

        return encode_minimum_distances(self)
