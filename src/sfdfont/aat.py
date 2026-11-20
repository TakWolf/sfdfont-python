from __future__ import annotations

from copy import copy, deepcopy
from typing import Any

from sfdfont.record import SfdRecord


class SfdState:
    next_state: int
    flags: int
    mark_lookup: str | None
    current_lookup: str | None
    mark_insert: list[str]
    current_insert: list[str]
    kern_values: list[int]

    def __init__(
        self,
        next_state: int = 0,
        flags: int = 0,
        mark_lookup: str | None = None,
        current_lookup: str | None = None,
        mark_insert: list[str] | None = None,
        current_insert: list[str] | None = None,
        kern_values: list[int] | None = None,
    ) -> None:
        self.next_state = next_state
        self.flags = flags
        self.mark_lookup = mark_lookup
        self.current_lookup = current_lookup
        self.mark_insert = mark_insert if mark_insert is not None else []
        self.current_insert = current_insert if current_insert is not None else []
        self.kern_values = kern_values if kern_values is not None else []

    def __copy__(self) -> SfdState:
        return SfdState(
            self.next_state,
            self.flags,
            self.mark_lookup,
            self.current_lookup,
            self.mark_insert,
            self.current_insert,
            self.kern_values,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdState:
        result = copy(self)
        memo[id(self)] = result
        result.next_state = deepcopy(self.next_state, memo)
        result.flags = deepcopy(self.flags, memo)
        result.mark_lookup = deepcopy(self.mark_lookup, memo)
        result.current_lookup = deepcopy(self.current_lookup, memo)
        result.mark_insert = deepcopy(self.mark_insert, memo)
        result.current_insert = deepcopy(self.current_insert, memo)
        result.kern_values = deepcopy(self.kern_values, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdState):
            return NotImplemented
        return (
            self.next_state == other.next_state
            and self.flags == other.flags
            and self.mark_lookup == other.mark_lookup
            and self.current_lookup == other.current_lookup
            and self.mark_insert == other.mark_insert
            and self.current_insert == other.current_insert
            and self.kern_values == other.kern_values
        )

    def copy(self) -> SfdState:
        return copy(self)

    def deepcopy(self) -> SfdState:
        return deepcopy(self)


class SfdStateMachine:
    keyword: str
    subtable: str | None
    feature: int
    setting: int
    flags: int
    classes: list[list[str] | None]
    states: list[list[SfdState]]

    def __init__(
        self,
        keyword: str = 'MacContext2:',
        subtable: str | None = None,
        feature: int = 0,
        setting: int = 0,
        flags: int = 0,
        classes: list[list[str] | None] | None = None,
        states: list[list[SfdState]] | None = None,
    ) -> None:
        self.keyword = keyword
        self.subtable = subtable
        self.feature = feature
        self.setting = setting
        self.flags = flags
        self.classes = classes if classes is not None else []
        self.states = states if states is not None else []

    def __copy__(self) -> SfdStateMachine:
        return SfdStateMachine(
            self.keyword,
            self.subtable,
            self.feature,
            self.setting,
            self.flags,
            self.classes,
            self.states,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdStateMachine:
        result = copy(self)
        memo[id(self)] = result
        result.keyword = deepcopy(self.keyword, memo)
        result.subtable = deepcopy(self.subtable, memo)
        result.feature = deepcopy(self.feature, memo)
        result.setting = deepcopy(self.setting, memo)
        result.flags = deepcopy(self.flags, memo)
        result.classes = deepcopy(self.classes, memo)
        result.states = deepcopy(self.states, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdStateMachine):
            return NotImplemented
        return (
            self.keyword == other.keyword
            and self.subtable == other.subtable
            and self.feature == other.feature
            and self.setting == other.setting
            and self.flags == other.flags
            and self.classes == other.classes
            and self.states == other.states
        )

    def copy(self) -> SfdStateMachine:
        return copy(self)

    def deepcopy(self) -> SfdStateMachine:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdStateMachine:
        from sfdfont._aat import decode_machine

        return decode_machine(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._aat import encode_machine

        return encode_machine(self)
