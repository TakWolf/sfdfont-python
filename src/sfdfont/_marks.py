import re

from sfdfont._layout import LayoutReader
from sfdfont._reader import Reader
from sfdfont._strings import decode_text, quote
from sfdfont.error import SfdParseError, SfdValidationError
from sfdfont.marks import SfdMarkClasses, SfdMarkGroup, SfdMarkSets
from sfdfont.record import SfdRecord

MARK_KEYS = {'MarkAttachClasses:', 'MarkAttachSets:'}


def parse_groups(reader: Reader, key: str) -> list[SfdMarkGroup]:
    stream = LayoutReader(reader)
    count = stream.count()
    if key == 'MarkAttachClasses:':
        if count < 1:
            reader.fail('mark classes require implicit class zero')
        count -= 1
    result = []
    for _ in range(count):
        name = stream.quoted()
        result.append(SfdMarkGroup(name, decode_text(stream.counted_text()).split()))
    return result


def mark_record(reader: Reader, key: str) -> SfdRecord:
    start = reader.pos
    parse_groups(reader, key)
    return SfdRecord(key, reader.data[start : reader.pos].lstrip())


def decode_groups(record: SfdRecord, key: str) -> list[SfdMarkGroup]:
    if record.keyword != key:
        raise SfdParseError('unexpected mark attachment record kind')
    reader = Reader(record.value)
    result = parse_groups(reader, key)
    if reader.word():
        reader.fail('trailing mark attachment data')
    return result


def decode_classes(record: SfdRecord) -> SfdMarkClasses:
    return SfdMarkClasses(decode_groups(record, 'MarkAttachClasses:'))


def decode_sets(record: SfdRecord) -> SfdMarkSets:
    return SfdMarkSets(decode_groups(record, 'MarkAttachSets:'))


def encode_groups(groups: list[SfdMarkGroup], key: str) -> SfdRecord:
    from sfdfont._writer import plain

    count = len(groups) + (key == 'MarkAttachClasses:')
    lines = [str(count).encode()]
    for group in groups:
        for glyph in group.glyphs:
            if not isinstance(glyph, str) or not re.fullmatch(r'[^\s\x00]+', glyph):
                raise SfdValidationError('invalid mark attachment glyph name')
        members = plain(' '.join(group.glyphs))
        lines.append(quote(group.name) + f' {len(members)} '.encode() + members)
    result = SfdRecord(key, b'\n'.join(lines))
    try:
        decode_groups(result, key)
    except SfdParseError as error:
        raise SfdValidationError(str(error)) from error
    return result


def encode_classes(value: SfdMarkClasses) -> SfdRecord:
    return encode_groups(value.classes, 'MarkAttachClasses:')


def encode_sets(value: SfdMarkSets) -> SfdRecord:
    return encode_groups(value.sets, 'MarkAttachSets:')


def validate_marks(font, lookups, contexts, legacy_flags=()) -> None:
    classes = sets = None
    try:
        for record in font.metadata.records:
            if record.keyword == 'MarkAttachClasses:':
                if classes is not None:
                    raise SfdValidationError('duplicate MarkAttachClasses table')
                classes = decode_classes(record).classes
            elif record.keyword == 'MarkAttachSets:':
                if sets is not None:
                    raise SfdValidationError('duplicate MarkAttachSets table')
                sets = decode_sets(record).sets
    except SfdParseError as error:
        raise SfdValidationError(str(error)) from error
    names = {glyph.name for glyph in font.iter_glyphs()}
    assignments = {}
    for is_class, groups in [(True, classes or []), (False, sets or [])]:
        for index, group in enumerate(groups):
            for name in group.glyphs:
                if name not in names:
                    raise SfdValidationError(f'unknown glyph {name!r} in mark attachment table')
                if is_class:
                    previous = assignments.setdefault(name, index)
                    if previous != index:
                        raise SfdValidationError(f'glyph {name!r} occurs in multiple mark attachment classes')
    flags_to_check = [
        *(lookup.flags for lookup in lookups),
        *(c.flags for c in contexts if c.subtable is None),
        *legacy_flags,
    ]
    for flags in flags_to_check:
        class_index = (flags >> 8) & 0xFF
        if class_index and class_index > len(classes or []):
            raise SfdValidationError(f'undefined mark attachment class index {class_index}')
        if flags & 0x10:
            set_index = (flags >> 16) & 0xFFFF
            if set_index >= len(sets or []):
                raise SfdValidationError(f'undefined mark filtering set index {set_index}')


def mark_identity(record):
    groups = decode_groups(record, record.keyword)
    return record.keyword, tuple(group.name for group in groups)
