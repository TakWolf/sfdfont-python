"""Editable layout values with explicit conversion to and from encoded SFD records.

Changing these objects does not change a font until to_record() replaces or adds
an entry in font.metadata.records. No implicit synchronization is performed.
"""

from __future__ import annotations

from copy import copy, deepcopy
from typing import Any

from sfdfont.record import SfdRecord


class SfdLookupSubtable:
    name: str
    suffix: str | None
    vertical: bool | None
    separation: int | None
    minimum_kerning: int | None
    kerning_flags: int

    def __init__(
        self,
        name: str,
        suffix: str | None = None,
        vertical: bool | None = None,
        separation: int | None = None,
        minimum_kerning: int | None = None,
        kerning_flags: int = 0,
    ) -> None:
        self.name = name
        self.suffix = suffix
        self.vertical = vertical
        self.separation = separation
        self.minimum_kerning = minimum_kerning
        self.kerning_flags = kerning_flags

    def __copy__(self) -> SfdLookupSubtable:
        return SfdLookupSubtable(
            self.name,
            self.suffix,
            self.vertical,
            self.separation,
            self.minimum_kerning,
            self.kerning_flags,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdLookupSubtable:
        result = copy(self)
        memo[id(self)] = result
        result.name = deepcopy(self.name, memo)
        result.suffix = deepcopy(self.suffix, memo)
        result.vertical = deepcopy(self.vertical, memo)
        result.separation = deepcopy(self.separation, memo)
        result.minimum_kerning = deepcopy(self.minimum_kerning, memo)
        result.kerning_flags = deepcopy(self.kerning_flags, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdLookupSubtable):
            return NotImplemented
        return (
            self.name == other.name
            and self.suffix == other.suffix
            and self.vertical == other.vertical
            and self.separation == other.separation
            and self.minimum_kerning == other.minimum_kerning
            and self.kerning_flags == other.kerning_flags
        )

    def copy(self) -> SfdLookupSubtable:
        return copy(self)

    def deepcopy(self) -> SfdLookupSubtable:
        return deepcopy(self)


class SfdLookupFeature:
    tag: str | tuple[int, int]
    scripts: dict[str, list[str]]

    def __init__(
        self,
        tag: str | tuple[int, int],
        scripts: dict[str, list[str]] | None = None,
    ) -> None:
        self.tag = tag
        self.scripts = scripts if scripts is not None else {}

    def __copy__(self) -> SfdLookupFeature:
        return SfdLookupFeature(
            self.tag,
            self.scripts,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdLookupFeature:
        result = copy(self)
        memo[id(self)] = result
        result.tag = deepcopy(self.tag, memo)
        result.scripts = deepcopy(self.scripts, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdLookupFeature):
            return NotImplemented
        return self.tag == other.tag and self.scripts == other.scripts

    def copy(self) -> SfdLookupFeature:
        return copy(self)

    def deepcopy(self) -> SfdLookupFeature:
        return deepcopy(self)


class SfdLookup:
    lookup_type: int
    name: str
    flags: int
    store_in_afm: bool
    subtables: list[SfdLookupSubtable]
    features: list[SfdLookupFeature]

    def __init__(
        self,
        lookup_type: int,
        name: str,
        flags: int = 0,
        store_in_afm: bool = False,
        subtables: list[SfdLookupSubtable] | None = None,
        features: list[SfdLookupFeature] | None = None,
    ) -> None:
        self.lookup_type = lookup_type
        self.name = name
        self.flags = flags
        self.store_in_afm = store_in_afm
        self.subtables = subtables if subtables is not None else []
        self.features = features if features is not None else []

    def __copy__(self) -> SfdLookup:
        return SfdLookup(
            self.lookup_type,
            self.name,
            self.flags,
            self.store_in_afm,
            self.subtables,
            self.features,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdLookup:
        result = copy(self)
        memo[id(self)] = result
        result.lookup_type = deepcopy(self.lookup_type, memo)
        result.name = deepcopy(self.name, memo)
        result.flags = deepcopy(self.flags, memo)
        result.store_in_afm = deepcopy(self.store_in_afm, memo)
        result.subtables = deepcopy(self.subtables, memo)
        result.features = deepcopy(self.features, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdLookup):
            return NotImplemented
        return (
            self.lookup_type == other.lookup_type
            and self.name == other.name
            and self.flags == other.flags
            and self.store_in_afm == other.store_in_afm
            and self.subtables == other.subtables
            and self.features == other.features
        )

    def copy(self) -> SfdLookup:
        return copy(self)

    def deepcopy(self) -> SfdLookup:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdLookup:
        from sfdfont._layout_models import decode_lookup

        return decode_lookup(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._layout_models import encode_lookup

        return encode_lookup(self)


class SfdSequenceLookup:
    sequence: int
    lookup: str | None

    def __init__(
        self,
        sequence: int,
        lookup: str | None = None,
    ) -> None:
        self.sequence = sequence
        self.lookup = lookup

    def __copy__(self) -> SfdSequenceLookup:
        return SfdSequenceLookup(
            self.sequence,
            self.lookup,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdSequenceLookup:
        result = copy(self)
        memo[id(self)] = result
        result.sequence = deepcopy(self.sequence, memo)
        result.lookup = deepcopy(self.lookup, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdSequenceLookup):
            return NotImplemented
        return self.sequence == other.sequence and self.lookup == other.lookup

    def copy(self) -> SfdSequenceLookup:
        return copy(self)

    def deepcopy(self) -> SfdSequenceLookup:
        return deepcopy(self)


class SfdContextRule:
    inputs: list[str | int | list[str]]
    backtrack: list[str | int | list[str]]
    lookahead: list[str | int | list[str]]
    lookups: list[SfdSequenceLookup]
    replacements: list[str] | None

    def __init__(
        self,
        inputs: list[str | int | list[str]] | None = None,
        backtrack: list[str | int | list[str]] | None = None,
        lookahead: list[str | int | list[str]] | None = None,
        lookups: list[SfdSequenceLookup] | None = None,
        replacements: list[str] | None = None,
    ) -> None:
        self.inputs = inputs if inputs is not None else []
        self.backtrack = backtrack if backtrack is not None else []
        self.lookahead = lookahead if lookahead is not None else []
        self.lookups = lookups if lookups is not None else []
        self.replacements = replacements

    def __copy__(self) -> SfdContextRule:
        return SfdContextRule(
            self.inputs,
            self.backtrack,
            self.lookahead,
            self.lookups,
            self.replacements,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdContextRule:
        result = copy(self)
        memo[id(self)] = result
        result.inputs = deepcopy(self.inputs, memo)
        result.backtrack = deepcopy(self.backtrack, memo)
        result.lookahead = deepcopy(self.lookahead, memo)
        result.lookups = deepcopy(self.lookups, memo)
        result.replacements = deepcopy(self.replacements, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdContextRule):
            return NotImplemented
        return (
            self.inputs == other.inputs
            and self.backtrack == other.backtrack
            and self.lookahead == other.lookahead
            and self.lookups == other.lookups
            and self.replacements == other.replacements
        )

    def copy(self) -> SfdContextRule:
        return copy(self)

    def deepcopy(self) -> SfdContextRule:
        return deepcopy(self)


class SfdContext:
    keyword: str
    form: str
    subtable: str | None
    flags: int
    script_language_index: int
    tag: str | None
    input_classes: list[list[str] | None]
    backtrack_classes: list[list[str] | None]
    lookahead_classes: list[list[str] | None]
    rules: list[SfdContextRule]
    input_class_names: list[str] | None
    backtrack_class_names: list[str] | None
    lookahead_class_names: list[str] | None

    def __init__(
        self,
        keyword: str = 'ChainSub2:',
        form: str = 'glyph',
        subtable: str | None = None,
        flags: int = 0,
        script_language_index: int = 0,
        tag: str | None = None,
        input_classes: list[list[str] | None] | None = None,
        backtrack_classes: list[list[str] | None] | None = None,
        lookahead_classes: list[list[str] | None] | None = None,
        rules: list[SfdContextRule] | None = None,
        input_class_names: list[str] | None = None,
        backtrack_class_names: list[str] | None = None,
        lookahead_class_names: list[str] | None = None,
    ) -> None:
        self.keyword = keyword
        self.form = form
        self.subtable = subtable
        self.flags = flags
        self.script_language_index = script_language_index
        self.tag = tag
        self.input_classes = input_classes if input_classes is not None else []
        self.backtrack_classes = backtrack_classes if backtrack_classes is not None else []
        self.lookahead_classes = lookahead_classes if lookahead_classes is not None else []
        self.rules = rules if rules is not None else []
        self.input_class_names = input_class_names
        self.backtrack_class_names = backtrack_class_names
        self.lookahead_class_names = lookahead_class_names

    def __copy__(self) -> SfdContext:
        return SfdContext(
            self.keyword,
            self.form,
            self.subtable,
            self.flags,
            self.script_language_index,
            self.tag,
            self.input_classes,
            self.backtrack_classes,
            self.lookahead_classes,
            self.rules,
            self.input_class_names,
            self.backtrack_class_names,
            self.lookahead_class_names,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdContext:
        result = copy(self)
        memo[id(self)] = result
        result.keyword = deepcopy(self.keyword, memo)
        result.form = deepcopy(self.form, memo)
        result.subtable = deepcopy(self.subtable, memo)
        result.flags = deepcopy(self.flags, memo)
        result.script_language_index = deepcopy(self.script_language_index, memo)
        result.tag = deepcopy(self.tag, memo)
        result.input_classes = deepcopy(self.input_classes, memo)
        result.backtrack_classes = deepcopy(self.backtrack_classes, memo)
        result.lookahead_classes = deepcopy(self.lookahead_classes, memo)
        result.rules = deepcopy(self.rules, memo)
        result.input_class_names = deepcopy(self.input_class_names, memo)
        result.backtrack_class_names = deepcopy(self.backtrack_class_names, memo)
        result.lookahead_class_names = deepcopy(self.lookahead_class_names, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdContext):
            return NotImplemented
        return (
            self.keyword == other.keyword
            and self.form == other.form
            and self.subtable == other.subtable
            and self.flags == other.flags
            and self.script_language_index == other.script_language_index
            and self.tag == other.tag
            and self.input_classes == other.input_classes
            and self.backtrack_classes == other.backtrack_classes
            and self.lookahead_classes == other.lookahead_classes
            and self.rules == other.rules
            and self.input_class_names == other.input_class_names
            and self.backtrack_class_names == other.backtrack_class_names
            and self.lookahead_class_names == other.lookahead_class_names
        )

    def copy(self) -> SfdContext:
        return copy(self)

    def deepcopy(self) -> SfdContext:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdContext:
        from sfdfont._layout_models import decode_context

        return decode_context(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._layout_models import encode_context

        return encode_context(self)


class SfdKerningClass:
    keyword: str
    first_classes: list[list[str] | None]
    second_classes: list[list[str] | None]
    offsets: list[list[int]]
    subtable: str | None
    flags: int
    script_language_index: int
    first_flags: list[int]
    second_flags: list[int]
    first_names: list[str | None]
    second_names: list[str | None]
    offset_flags: list[list[int]]
    adjustments: dict[tuple[int, int], dict[int, int]]

    def __init__(
        self,
        keyword: str = 'KernClass2:',
        first_classes: list[list[str] | None] | None = None,
        second_classes: list[list[str] | None] | None = None,
        offsets: list[list[int]] | None = None,
        subtable: str | None = None,
        flags: int = 0,
        script_language_index: int = 0,
        first_flags: list[int] | None = None,
        second_flags: list[int] | None = None,
        first_names: list[str | None] | None = None,
        second_names: list[str | None] | None = None,
        offset_flags: list[list[int]] | None = None,
        adjustments: dict[tuple[int, int], dict[int, int]] | None = None,
    ) -> None:
        self.keyword = keyword
        self.first_classes = first_classes if first_classes is not None else []
        self.second_classes = second_classes if second_classes is not None else []
        self.offsets = offsets if offsets is not None else []
        self.subtable = subtable
        self.flags = flags
        self.script_language_index = script_language_index
        self.first_flags = first_flags if first_flags is not None else []
        self.second_flags = second_flags if second_flags is not None else []
        self.first_names = first_names if first_names is not None else []
        self.second_names = second_names if second_names is not None else []
        self.offset_flags = offset_flags if offset_flags is not None else []
        self.adjustments = adjustments if adjustments is not None else {}

    def __copy__(self) -> SfdKerningClass:
        return SfdKerningClass(
            self.keyword,
            self.first_classes,
            self.second_classes,
            self.offsets,
            self.subtable,
            self.flags,
            self.script_language_index,
            self.first_flags,
            self.second_flags,
            self.first_names,
            self.second_names,
            self.offset_flags,
            self.adjustments,
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> SfdKerningClass:
        result = copy(self)
        memo[id(self)] = result
        result.keyword = deepcopy(self.keyword, memo)
        result.first_classes = deepcopy(self.first_classes, memo)
        result.second_classes = deepcopy(self.second_classes, memo)
        result.offsets = deepcopy(self.offsets, memo)
        result.subtable = deepcopy(self.subtable, memo)
        result.flags = deepcopy(self.flags, memo)
        result.script_language_index = deepcopy(self.script_language_index, memo)
        result.first_flags = deepcopy(self.first_flags, memo)
        result.second_flags = deepcopy(self.second_flags, memo)
        result.first_names = deepcopy(self.first_names, memo)
        result.second_names = deepcopy(self.second_names, memo)
        result.offset_flags = deepcopy(self.offset_flags, memo)
        result.adjustments = deepcopy(self.adjustments, memo)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SfdKerningClass):
            return NotImplemented
        return (
            self.keyword == other.keyword
            and self.first_classes == other.first_classes
            and self.second_classes == other.second_classes
            and self.offsets == other.offsets
            and self.subtable == other.subtable
            and self.flags == other.flags
            and self.script_language_index == other.script_language_index
            and self.first_flags == other.first_flags
            and self.second_flags == other.second_flags
            and self.first_names == other.first_names
            and self.second_names == other.second_names
            and self.offset_flags == other.offset_flags
            and self.adjustments == other.adjustments
        )

    def copy(self) -> SfdKerningClass:
        return copy(self)

    def deepcopy(self) -> SfdKerningClass:
        return deepcopy(self)

    @staticmethod
    def from_record(record: SfdRecord) -> SfdKerningClass:
        from sfdfont._layout_models import decode_kern_class

        return decode_kern_class(record)

    def to_record(self) -> SfdRecord:
        from sfdfont._layout_models import encode_kern_class

        return encode_kern_class(self)
