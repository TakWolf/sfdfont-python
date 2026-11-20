from __future__ import annotations

from copy import copy, deepcopy
from typing import Any

from sfdfont.record import SfdRecord


class SfdBaselineExtent:
    tag: str | None
    descent: int
    ascent: int
    depth: int

    def __init__(
        self,
        tag: str | None = None,
        descent: int = 0,
        ascent: int = 0,
        depth: int = 0,
    ) -> None:
        self.tag = tag
        self.descent = descent
        self.ascent = ascent
        self.depth = depth

    def __copy__(self) -> SfdBaselineExtent:
        return SfdBaselineExtent(
            self.tag,
            self.descent,
            self.ascent,
            self.depth,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdBaselineExtent:
        result = copy(self)
        memo[id(self)] = result
        result.tag = deepcopy(self.tag, memo)
        result.descent = deepcopy(self.descent, memo)
        result.ascent = deepcopy(self.ascent, memo)
        result.depth = deepcopy(self.depth, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdBaselineExtent):
            return NotImplemented
        return (
            self.tag == other.tag
            and self.descent == other.descent
            and self.ascent == other.ascent
            and self.depth == other.depth
        )

    def __repr__(self) -> str:
        return (
            f'SfdBaselineExtent('
            f'tag={self.tag!r}, '
            f'descent={self.descent!r}, '
            f'ascent={self.ascent!r}, '
            f'depth={self.depth!r}'
            f')'
        )

    def copy(self) -> SfdBaselineExtent:
        return copy(self)

    def deepcopy(self) -> SfdBaselineExtent:
        return deepcopy(self)


class SfdBaselineScript:
    tag: str
    default_baseline: int
    positions: list[int]
    extents: list[SfdBaselineExtent]

    def __init__(
        self,
        tag: str = 'latn',
        default_baseline: int = 0,
        positions: list[int] | None = None,
        extents: list[SfdBaselineExtent] | None = None,
    ) -> None:
        self.tag = tag
        self.default_baseline = default_baseline
        self.positions = positions if positions is not None else []
        self.extents = extents if extents is not None else []

    def __copy__(self) -> SfdBaselineScript:
        return SfdBaselineScript(
            self.tag,
            self.default_baseline,
            self.positions,
            self.extents,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdBaselineScript:
        result = copy(self)
        memo[id(self)] = result
        result.tag = deepcopy(self.tag, memo)
        result.default_baseline = deepcopy(self.default_baseline, memo)
        result.positions = deepcopy(self.positions, memo)
        result.extents = deepcopy(self.extents, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdBaselineScript):
            return NotImplemented
        return (
            self.tag == other.tag
            and self.default_baseline == other.default_baseline
            and self.positions == other.positions
            and self.extents == other.extents
        )

    def __repr__(self) -> str:
        return (
            f'SfdBaselineScript('
            f'tag={self.tag!r}, '
            f'default_baseline={self.default_baseline!r}, '
            f'positions={self.positions!r}, '
            f'extents={self.extents!r}'
            f')'
        )

    def copy(self) -> SfdBaselineScript:
        return copy(self)

    def deepcopy(self) -> SfdBaselineScript:
        return deepcopy(self)


class SfdBaselines:
    keyword: str
    tags: list[str]
    scripts: list[SfdBaselineScript]

    def __init__(
        self,
        keyword: str = 'BaseHoriz:',
        tags: list[str] | None = None,
        scripts: list[SfdBaselineScript] | None = None,
    ) -> None:
        self.keyword = keyword
        self.tags = tags if tags is not None else []
        self.scripts = scripts if scripts is not None else []

    def __copy__(self) -> SfdBaselines:
        return SfdBaselines(
            self.keyword,
            self.tags,
            self.scripts,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdBaselines:
        result = copy(self)
        memo[id(self)] = result
        result.keyword = deepcopy(self.keyword, memo)
        result.tags = deepcopy(self.tags, memo)
        result.scripts = deepcopy(self.scripts, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdBaselines):
            return NotImplemented
        return self.keyword == other.keyword and self.tags == other.tags and self.scripts == other.scripts

    def __repr__(self) -> str:
        return f'SfdBaselines(keyword={self.keyword!r}, tags={self.tags!r}, scripts={self.scripts!r})'

    def copy(self) -> SfdBaselines:
        return copy(self)

    def deepcopy(self) -> SfdBaselines:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdBaselines:
        from sfdfont._baselines import decode_baselines

        return decode_baselines(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._baselines import encode_baselines

        return encode_baselines(self)
