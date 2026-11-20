from __future__ import annotations

from copy import copy, deepcopy
from typing import Any

from sfdfont.record import SfdRecord


class SfdFeatureName:
    language: int
    name: str
    tooltip: str | None
    sample: str | None
    parameters: list[str] | None

    def __init__(
        self,
        language: int = 0x0409,
        name: str = '',
        tooltip: str | None = None,
        sample: str | None = None,
        parameters: list[str] | None = None,
    ) -> None:
        self.language = language
        self.name = name
        self.tooltip = tooltip
        self.sample = sample
        self.parameters = parameters

    def __copy__(self) -> SfdFeatureName:
        return SfdFeatureName(
            self.language,
            self.name,
            self.tooltip,
            self.sample,
            self.parameters,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdFeatureName:
        result = copy(self)
        memo[id(self)] = result
        result.language = deepcopy(self.language, memo)
        result.name = deepcopy(self.name, memo)
        result.tooltip = deepcopy(self.tooltip, memo)
        result.sample = deepcopy(self.sample, memo)
        result.parameters = deepcopy(self.parameters, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdFeatureName):
            return NotImplemented
        return (
            self.language == other.language
            and self.name == other.name
            and self.tooltip == other.tooltip
            and self.sample == other.sample
            and self.parameters == other.parameters
        )

    def __repr__(self) -> str:
        return (
            f'SfdFeatureName('
            f'language={self.language!r}, '
            f'name={self.name!r}, '
            f'tooltip={self.tooltip!r}, '
            f'sample={self.sample!r}, '
            f'parameters={self.parameters!r}'
            f')'
        )

    def copy(self) -> SfdFeatureName:
        return copy(self)

    def deepcopy(self) -> SfdFeatureName:
        return deepcopy(self)


class SfdFeatureNames:
    tag: str
    names: list[SfdFeatureName]
    trailer: str | None

    def __init__(
        self,
        tag: str = 'ss01',
        names: list[SfdFeatureName] | None = None,
        trailer: str | None = None,
    ) -> None:
        self.tag = tag
        self.names = names if names is not None else []
        self.trailer = trailer

    def __copy__(self) -> SfdFeatureNames:
        return SfdFeatureNames(
            self.tag,
            self.names,
            self.trailer,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdFeatureNames:
        result = copy(self)
        memo[id(self)] = result
        result.tag = deepcopy(self.tag, memo)
        result.names = deepcopy(self.names, memo)
        result.trailer = deepcopy(self.trailer, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdFeatureNames):
            return NotImplemented
        return self.tag == other.tag and self.names == other.names and self.trailer == other.trailer

    def __repr__(self) -> str:
        return f'SfdFeatureNames(tag={self.tag!r}, names={self.names!r}, trailer={self.trailer!r})'

    def copy(self) -> SfdFeatureNames:
        return copy(self)

    def deepcopy(self) -> SfdFeatureNames:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdFeatureNames:
        from sfdfont._feature_names import decode_feature_names

        return decode_feature_names(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._feature_names import encode_feature_names

        return encode_feature_names(self)
