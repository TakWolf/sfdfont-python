from __future__ import annotations

from copy import copy, deepcopy
from typing import Any

from sfdfont.record import SfdRecord


class SfdJustificationPriority:
    enable_shrink: list[str] | None
    disable_shrink: list[str] | None
    max_shrink: list[str] | None
    enable_extend: list[str] | None
    disable_extend: list[str] | None
    max_extend: list[str] | None

    def __init__(
        self,
        enable_shrink: list[str] | None = None,
        disable_shrink: list[str] | None = None,
        max_shrink: list[str] | None = None,
        enable_extend: list[str] | None = None,
        disable_extend: list[str] | None = None,
        max_extend: list[str] | None = None,
    ) -> None:
        self.enable_shrink = enable_shrink
        self.disable_shrink = disable_shrink
        self.max_shrink = max_shrink
        self.enable_extend = enable_extend
        self.disable_extend = disable_extend
        self.max_extend = max_extend

    def __copy__(self) -> SfdJustificationPriority:
        return SfdJustificationPriority(
            self.enable_shrink,
            self.disable_shrink,
            self.max_shrink,
            self.enable_extend,
            self.disable_extend,
            self.max_extend,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdJustificationPriority:
        result = copy(self)
        memo[id(self)] = result
        result.enable_shrink = deepcopy(self.enable_shrink, memo)
        result.disable_shrink = deepcopy(self.disable_shrink, memo)
        result.max_shrink = deepcopy(self.max_shrink, memo)
        result.enable_extend = deepcopy(self.enable_extend, memo)
        result.disable_extend = deepcopy(self.disable_extend, memo)
        result.max_extend = deepcopy(self.max_extend, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdJustificationPriority):
            return NotImplemented
        return (
            self.enable_shrink == other.enable_shrink
            and self.disable_shrink == other.disable_shrink
            and self.max_shrink == other.max_shrink
            and self.enable_extend == other.enable_extend
            and self.disable_extend == other.disable_extend
            and self.max_extend == other.max_extend
        )

    def __repr__(self) -> str:
        return (
            f'SfdJustificationPriority('
            f'enable_shrink={self.enable_shrink!r}, '
            f'disable_shrink={self.disable_shrink!r}, '
            f'max_shrink={self.max_shrink!r}, '
            f'enable_extend={self.enable_extend!r}, '
            f'disable_extend={self.disable_extend!r}, '
            f'max_extend={self.max_extend!r}'
            f')'
        )

    def copy(self) -> SfdJustificationPriority:
        return copy(self)

    def deepcopy(self) -> SfdJustificationPriority:
        return deepcopy(self)


class SfdJustificationLanguage:
    tag: str
    priorities: list[SfdJustificationPriority]

    def __init__(
        self,
        tag: str = 'dflt',
        priorities: list[SfdJustificationPriority] | None = None,
    ) -> None:
        self.tag = tag
        self.priorities = priorities if priorities is not None else []

    def __copy__(self) -> SfdJustificationLanguage:
        return SfdJustificationLanguage(
            self.tag,
            self.priorities,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdJustificationLanguage:
        result = copy(self)
        memo[id(self)] = result
        result.tag = deepcopy(self.tag, memo)
        result.priorities = deepcopy(self.priorities, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdJustificationLanguage):
            return NotImplemented
        return self.tag == other.tag and self.priorities == other.priorities

    def __repr__(self) -> str:
        return f'SfdJustificationLanguage(tag={self.tag!r}, priorities={self.priorities!r})'

    def copy(self) -> SfdJustificationLanguage:
        return copy(self)

    def deepcopy(self) -> SfdJustificationLanguage:
        return deepcopy(self)


class SfdJustificationScript:
    tag: str
    extenders: list[str] | None
    languages: list[SfdJustificationLanguage]

    def __init__(
        self,
        tag: str = 'latn',
        extenders: list[str] | None = None,
        languages: list[SfdJustificationLanguage] | None = None,
    ) -> None:
        self.tag = tag
        self.extenders = extenders
        self.languages = languages if languages is not None else []

    def __copy__(self) -> SfdJustificationScript:
        return SfdJustificationScript(
            self.tag,
            self.extenders,
            self.languages,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdJustificationScript:
        result = copy(self)
        memo[id(self)] = result
        result.tag = deepcopy(self.tag, memo)
        result.extenders = deepcopy(self.extenders, memo)
        result.languages = deepcopy(self.languages, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdJustificationScript):
            return NotImplemented
        return self.tag == other.tag and self.extenders == other.extenders and self.languages == other.languages

    def __repr__(self) -> str:
        return f'SfdJustificationScript(tag={self.tag!r}, extenders={self.extenders!r}, languages={self.languages!r})'

    def copy(self) -> SfdJustificationScript:
        return copy(self)

    def deepcopy(self) -> SfdJustificationScript:
        return deepcopy(self)


class SfdJustification:
    scripts: list[SfdJustificationScript]

    def __init__(
        self,
        scripts: list[SfdJustificationScript] | None = None,
    ) -> None:
        self.scripts = scripts if scripts is not None else []

    def __copy__(self) -> SfdJustification:
        return SfdJustification(
            self.scripts,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdJustification:
        result = copy(self)
        memo[id(self)] = result
        result.scripts = deepcopy(self.scripts, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdJustification):
            return NotImplemented
        return self.scripts == other.scripts

    def __repr__(self) -> str:
        return f'SfdJustification(scripts={self.scripts!r})'

    def copy(self) -> SfdJustification:
        return copy(self)

    def deepcopy(self) -> SfdJustification:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdJustification:
        from sfdfont._justification import decode_justification

        return decode_justification(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._justification import encode_justification

        return encode_justification(self)
