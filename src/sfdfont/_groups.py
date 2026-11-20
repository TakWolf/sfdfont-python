from sfdfont._layout import LayoutReader
from sfdfont._reader import Reader
from sfdfont._strings import quote
from sfdfont.error import SfdParseError, SfdValidationError
from sfdfont.groups import SfdGlyphGroup, SfdGroupKerningPair
from sfdfont.record import SfdRecord

GROUP_KEYS = {'Group:', 'GroupKern:', 'GroupVKern:'}


def decode_group(item):
    if item.keyword != 'Group:':
        raise SfdParseError('unexpected glyph group record kind')
    reader = Reader(item.value)
    stream = LayoutReader(reader)
    name = stream.quoted()
    glyphs = stream.quoted().split()
    if stream.peek():
        reader.fail('trailing glyph group data')
    return SfdGlyphGroup(name, glyphs)


def decode_group_pair(item):
    if item.keyword not in {'GroupKern:', 'GroupVKern:'}:
        raise SfdParseError('unexpected group kerning record kind')
    reader = Reader(item.value)
    stream = LayoutReader(reader)
    result = SfdGroupKerningPair(
        item.keyword, stream.quoted(), stream.quoted(), stream.integer(-0x80000000, 0x7FFFFFFF)
    )
    if stream.peek():
        reader.fail('trailing group kerning data')
    return result


def checked(item, value, decode):
    try:
        if decode(item) != value:
            raise SfdValidationError('group fields would change interpretation when written')
    except SfdParseError as error:
        raise SfdValidationError(str(error)) from error
    return item


def encode_group(value):
    from sfdfont._validation import check

    # Membership is a quoted, whitespace-separated list, not a counted layout class.
    check(
        all(
            isinstance(name, str) and name and not any(c.isspace() or c == '\0' for c in name) for name in value.glyphs
        ),
        'invalid glyph group member',
    )
    item = SfdRecord('Group:', quote(value.name) + b' ' + quote(' '.join(value.glyphs)))
    return checked(item, value, decode_group)


def encode_group_pair(value):
    from sfdfont._validation import check, number

    check(value.keyword in {'GroupKern:', 'GroupVKern:'}, 'invalid group kerning keyword')
    number(value.offset, 'raw group kerning offset', -0x80000000, 0x7FFFFFFF)
    item = SfdRecord(value.keyword, quote(value.left) + b' ' + quote(value.right) + b' ' + str(value.offset).encode())
    return checked(item, value, decode_group_pair)


def group_record(reader, key):
    item = SfdRecord(key, reader.line())
    decode_group(item) if key == 'Group:' else decode_group_pair(item)
    return item


def group_identity(records):
    result = []
    for item in records:
        if item.keyword == 'Group:':
            group = decode_group(item)
            result.append((item.keyword, group.name, group.glyphs))
        elif item.keyword in {'GroupKern:', 'GroupVKern:'}:
            pair = decode_group_pair(item)
            result.append((item.keyword, pair.left, pair.right))
    return result


def group_class_identity(records):
    from sfdfont._layout import KERN_CLASS_KEYS
    from sfdfont.layout import SfdKerningClass

    if not any(item.keyword in GROUP_KEYS for item in records):
        return []
    result = []
    for item in records:
        if item.keyword in KERN_CLASS_KEYS:
            value = SfdKerningClass.from_record(item)
            result.append((item.keyword, value.first_names, value.second_names))
    return result


def validate_groups(font):
    try:
        for item in font.metadata.records:
            if item.keyword in GROUP_KEYS:
                decode_group(item) if item.keyword == 'Group:' else decode_group_pair(item)
    except SfdParseError as error:
        raise SfdValidationError(str(error)) from error
