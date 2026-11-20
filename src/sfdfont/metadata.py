from __future__ import annotations

from copy import copy, deepcopy
from typing import Any

from sfdfont.legacy_names import SfdStyleMapName
from sfdfont.metrics import SfdFontMetric, SfdFontRealMetric
from sfdfont.record import SfdRecord


class SfdLanguageNames:
    language: int
    names: list[str]
    style_map_family_names: list[SfdStyleMapName]

    def __init__(
        self,
        language: int,
        names: list[str] | None = None,
        style_map_family_names: list[SfdStyleMapName] | None = None,
    ) -> None:
        self.language = language
        self.names = names if names is not None else []
        self.style_map_family_names = style_map_family_names if style_map_family_names is not None else []

    def __copy__(self) -> SfdLanguageNames:
        return SfdLanguageNames(
            self.language,
            self.names,
            self.style_map_family_names,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdLanguageNames:
        copied = copy(self)
        memo[id(self)] = copied
        copied.language = deepcopy(self.language, memo)
        copied.names = deepcopy(self.names, memo)
        copied.style_map_family_names = deepcopy(self.style_map_family_names, memo)
        return copied

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdLanguageNames):
            return NotImplemented
        return (
            self.language == other.language
            and self.names == other.names
            and self.style_map_family_names == other.style_map_family_names
        )

    def __repr__(self) -> str:
        return (
            f'SfdLanguageNames(language={self.language!r}, names={self.names!r}, '
            f'style_map_family_names={self.style_map_family_names!r})'
        )

    def copy(self) -> SfdLanguageNames:
        return copy(self)

    def deepcopy(self) -> SfdLanguageNames:
        return deepcopy(self)


class SfdMetadata:
    font_name: str
    full_name: str
    family_name: str
    weight: str
    copyright: str
    version: str
    ascent: int
    descent: int
    encoding: str
    comments: str | None
    font_log: str | None
    language_names: list[SfdLanguageNames]
    records: list[SfdRecord]

    def __init__(
        self,
        font_name: str = 'Untitled',
        full_name: str = 'Untitled',
        family_name: str = 'Untitled',
        weight: str = 'Regular',
        copyright: str = '',
        version: str = '001.000',
        ascent: int = 800,
        descent: int = 200,
        encoding: str = 'UnicodeFull',
        comments: str | None = None,
        font_log: str | None = None,
        language_names: list[SfdLanguageNames] | None = None,
        records: list[SfdRecord] | None = None,
    ) -> None:
        self.font_name = font_name
        self.full_name = full_name
        self.family_name = family_name
        self.weight = weight
        self.copyright = copyright
        self.version = version
        self.ascent = ascent
        self.descent = descent
        self.encoding = encoding
        self.comments = comments
        self.font_log = font_log
        self.language_names = language_names if language_names is not None else []
        self.records = records if records is not None else []

    def __copy__(self) -> SfdMetadata:
        return SfdMetadata(
            self.font_name,
            self.full_name,
            self.family_name,
            self.weight,
            self.copyright,
            self.version,
            self.ascent,
            self.descent,
            self.encoding,
            self.comments,
            self.font_log,
            self.language_names,
            self.records,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdMetadata:
        copied = copy(self)
        memo[id(self)] = copied
        copied.font_name = deepcopy(self.font_name, memo)
        copied.full_name = deepcopy(self.full_name, memo)
        copied.family_name = deepcopy(self.family_name, memo)
        copied.weight = deepcopy(self.weight, memo)
        copied.copyright = deepcopy(self.copyright, memo)
        copied.version = deepcopy(self.version, memo)
        copied.ascent = deepcopy(self.ascent, memo)
        copied.descent = deepcopy(self.descent, memo)
        copied.encoding = deepcopy(self.encoding, memo)
        copied.comments = deepcopy(self.comments, memo)
        copied.font_log = deepcopy(self.font_log, memo)
        copied.language_names = deepcopy(self.language_names, memo)
        copied.records = deepcopy(self.records, memo)
        return copied

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdMetadata):
            return NotImplemented
        return (
            self.font_name == other.font_name
            and self.full_name == other.full_name
            and self.family_name == other.family_name
            and self.weight == other.weight
            and self.copyright == other.copyright
            and self.version == other.version
            and self.ascent == other.ascent
            and self.descent == other.descent
            and self.encoding == other.encoding
            and self.comments == other.comments
            and self.font_log == other.font_log
            and self.language_names == other.language_names
            and self.records == other.records
        )

    def __repr__(self) -> str:
        return (
            f'SfdMetadata('
            f'font_name={self.font_name!r}, '
            f'full_name={self.full_name!r}, '
            f'family_name={self.family_name!r}, '
            f'weight={self.weight!r}, '
            f'copyright={self.copyright!r}, '
            f'version={self.version!r}, '
            f'ascent={self.ascent!r}, '
            f'descent={self.descent!r}, '
            f'encoding={self.encoding!r}, '
            f'comments={self.comments!r}, '
            f'font_log={self.font_log!r}, '
            f'language_names={self.language_names!r}, '
            f'records={self.records!r}'
            f')'
        )

    def copy(self) -> SfdMetadata:
        return copy(self)

    def deepcopy(self) -> SfdMetadata:
        return deepcopy(self)

    def find_metric(self, keyword: str) -> SfdFontMetric | SfdFontRealMetric | None:
        """Decode an independent metric, including historical keyword aliases."""
        from sfdfont._metrics import REAL_KEYS, SCALAR_KEYS, metric_key
        from sfdfont.error import SfdValidationError

        if keyword not in SCALAR_KEYS | REAL_KEYS:
            raise SfdValidationError('invalid font metric keyword')
        items = [item for item in self.records if metric_key(item.keyword) == metric_key(keyword)]
        if len(items) > 1:
            raise SfdValidationError('duplicate font metric')
        if not items:
            return None
        return SfdFontRealMetric.from_record(items[0]) if keyword in REAL_KEYS else SfdFontMetric.from_record(items[0])

    def set_metric(self, metric: SfdFontMetric | SfdFontRealMetric) -> None:
        """Replace a metric or append it, preserving all other encoded records."""
        from sfdfont._metrics import metric_key
        from sfdfont.error import SfdValidationError

        replacement = metric.to_record()
        indices = [i for i, item in enumerate(self.records) if metric_key(item.keyword) == metric_key(metric.keyword)]
        if len(indices) > 1:
            raise SfdValidationError('duplicate font metric')
        if indices:
            self.records[indices[0]] = replacement
        else:
            self.records.append(replacement)
