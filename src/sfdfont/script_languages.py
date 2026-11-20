from __future__ import annotations

from copy import copy, deepcopy
from typing import Any

from sfdfont.record import SfdRecord


class SfdScriptLanguage:
    script: str
    languages: list[str]

    def __init__(
        self,
        script: str = 'latn',
        languages: list[str] | None = None,
    ) -> None:
        self.script = script
        self.languages = languages if languages is not None else []

    def __copy__(self) -> SfdScriptLanguage:
        return SfdScriptLanguage(
            self.script,
            self.languages,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdScriptLanguage:
        result = copy(self)
        memo[id(self)] = result
        result.script = deepcopy(self.script, memo)
        result.languages = deepcopy(self.languages, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdScriptLanguage):
            return NotImplemented
        return self.script == other.script and self.languages == other.languages

    def __repr__(self) -> str:
        return f'SfdScriptLanguage(script={self.script!r}, languages={self.languages!r})'

    def copy(self) -> SfdScriptLanguage:
        return copy(self)

    def deepcopy(self) -> SfdScriptLanguage:
        return deepcopy(self)


class SfdScriptLanguages:
    lists: list[list[SfdScriptLanguage]]

    def __init__(
        self,
        lists: list[list[SfdScriptLanguage]] | None = None,
    ) -> None:
        self.lists = lists if lists is not None else []

    def __copy__(self) -> SfdScriptLanguages:
        return SfdScriptLanguages(
            self.lists,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdScriptLanguages:
        result = copy(self)
        memo[id(self)] = result
        result.lists = deepcopy(self.lists, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdScriptLanguages):
            return NotImplemented
        return self.lists == other.lists

    def __repr__(self) -> str:
        return f'SfdScriptLanguages(lists={self.lists!r})'

    def copy(self) -> SfdScriptLanguages:
        return copy(self)

    def deepcopy(self) -> SfdScriptLanguages:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdScriptLanguages:
        from sfdfont._script_languages import decode_script_languages

        return decode_script_languages(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._script_languages import encode_script_languages

        return encode_script_languages(self)
