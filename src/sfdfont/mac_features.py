from __future__ import annotations

from copy import copy, deepcopy
from typing import Any

from sfdfont.record import SfdRecord
from sfdfont.variation import SfdMacName


class SfdMacSetting:
    setting: int
    names: list[SfdMacName]

    def __init__(
        self,
        setting: int = 0,
        names: list[SfdMacName] | None = None,
    ) -> None:
        self.setting = setting
        self.names = names if names is not None else []

    def __copy__(self) -> SfdMacSetting:
        return SfdMacSetting(
            self.setting,
            self.names,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdMacSetting:
        result = copy(self)
        memo[id(self)] = result
        result.setting = deepcopy(self.setting, memo)
        result.names = deepcopy(self.names, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdMacSetting):
            return NotImplemented
        return self.setting == other.setting and self.names == other.names

    def __repr__(self) -> str:
        return f'SfdMacSetting(setting={self.setting!r}, names={self.names!r})'

    def copy(self) -> SfdMacSetting:
        return copy(self)

    def deepcopy(self) -> SfdMacSetting:
        return deepcopy(self)


class SfdMacFeature:
    feature: int
    is_mutex: bool
    default_setting: int
    names: list[SfdMacName]
    settings: list[SfdMacSetting]

    def __init__(
        self,
        feature: int = 0,
        is_mutex: bool = True,
        default_setting: int = 0,
        names: list[SfdMacName] | None = None,
        settings: list[SfdMacSetting] | None = None,
    ) -> None:
        self.feature = feature
        self.is_mutex = is_mutex
        self.default_setting = default_setting
        self.names = names if names is not None else []
        self.settings = settings if settings is not None else []

    def __copy__(self) -> SfdMacFeature:
        return SfdMacFeature(
            self.feature,
            self.is_mutex,
            self.default_setting,
            self.names,
            self.settings,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdMacFeature:
        result = copy(self)
        memo[id(self)] = result
        result.feature = deepcopy(self.feature, memo)
        result.is_mutex = deepcopy(self.is_mutex, memo)
        result.default_setting = deepcopy(self.default_setting, memo)
        result.names = deepcopy(self.names, memo)
        result.settings = deepcopy(self.settings, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdMacFeature):
            return NotImplemented
        return (
            self.feature == other.feature
            and self.is_mutex == other.is_mutex
            and self.default_setting == other.default_setting
            and self.names == other.names
            and self.settings == other.settings
        )

    def __repr__(self) -> str:
        return (
            f'SfdMacFeature('
            f'feature={self.feature!r}, '
            f'is_mutex={self.is_mutex!r}, '
            f'default_setting={self.default_setting!r}, '
            f'names={self.names!r}, '
            f'settings={self.settings!r}'
            f')'
        )

    def copy(self) -> SfdMacFeature:
        return copy(self)

    def deepcopy(self) -> SfdMacFeature:
        return deepcopy(self)


class SfdMacFeatures:
    features: list[SfdMacFeature]

    def __init__(
        self,
        features: list[SfdMacFeature] | None = None,
    ) -> None:
        self.features = features if features is not None else []

    def __copy__(self) -> SfdMacFeatures:
        return SfdMacFeatures(
            self.features,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdMacFeatures:
        result = copy(self)
        memo[id(self)] = result
        result.features = deepcopy(self.features, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdMacFeatures):
            return NotImplemented
        return self.features == other.features

    def __repr__(self) -> str:
        return f'SfdMacFeatures(features={self.features!r})'

    def copy(self) -> SfdMacFeatures:
        return copy(self)

    def deepcopy(self) -> SfdMacFeatures:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdMacFeatures:
        from sfdfont._mac_features import decode_mac_features

        return decode_mac_features(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._mac_features import encode_mac_features

        return encode_mac_features(self)
